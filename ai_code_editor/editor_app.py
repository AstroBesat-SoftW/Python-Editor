"""
editor_app.py
--------------
The main application window for Sotstech Python Editor: a professional,
multi-tab, AI-assisted Python code editor built with Tkinter.
"""

import os
import sys
import subprocess
import importlib
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import config
import theme
from console_redirector import ConsoleRedirector
from editor_tab import EditorTab
from ai_assistant import AIAssistant, AIAssistantError

WELCOME_SNIPPET = '''"""
Welcome to Sotstech Python Editor.

- Write or paste Python code here. Use the "+" button (or Ctrl+T) to
  open additional pages/tabs and work on several files at once.
- Click "Run" (or press F5) to execute the code in the current tab --
  output appears in the panel below. Calling input() works too: it
  opens a small dialog instead of freezing the app.
- Select a snippet and click "AI Suggest" (or press Ctrl+Space). Tell
  the AI what you want done with it, and review the result before
  deciding whether to apply it.
- Set your OpenAI key once from AI Assistant -> Add API Key. It is
  saved locally and you won't be asked again.
- Every file you open or save lives in the "dosyam" folder next to the
  app. Open the "demo.py" file there to try the import auto-suggestion:
  type "import " on a blank line and press Tab to accept the hint.
"""

def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("world"))
'''


class AICodeStudio:
    """Encapsulates the entire application: layout, state, and behaviour."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.ai_assistant = AIAssistant()

        self._configure_root()
        self._install_crash_guard()
        self._configure_ttk_styles()
        self._build_menu_bar()
        self._build_toolbar()
        self._build_main_layout()
        self._build_status_bar()
        self._bind_shortcuts()

        self.new_tab(initial_text=WELCOME_SNIPPET)
        self._update_title()

    # ------------------------------------------------------------------
    # Root window / global style setup
    # ------------------------------------------------------------------
    def _configure_root(self):
        self.root.title(config.APP_DISPLAY_TITLE)
        self.root.geometry(config.DEFAULT_WINDOW_SIZE)
        self.root.minsize(*config.MIN_WINDOW_SIZE)
        self.root.configure(bg=theme.BG_APP)

    def _configure_ttk_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=theme.BG_PANEL)
        style.configure("Toolbar.TFrame", background=theme.BG_PANEL)
        style.configure("Status.TFrame", background=theme.BG_STATUSBAR)

        style.configure(
            "Accent.TButton",
            background=theme.ACCENT,
            foreground="#ffffff",
            font=theme.FONT_UI_BOLD,
            padding=(14, 8),
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", theme.ACCENT_HOVER), ("pressed", theme.ACCENT_ACTIVE)],
        )

        style.configure(
            "Secondary.TButton",
            background=theme.BUTTON_SECONDARY_BG,
            foreground=theme.FG_EDITOR,
            font=theme.FONT_UI,
            padding=(14, 8),
            borderwidth=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", theme.BUTTON_SECONDARY_HOVER)],
        )

        style.configure(
            "Icon.TButton",
            background=theme.BG_PANEL,
            foreground=theme.FG_EDITOR,
            font=theme.FONT_UI_BOLD,
            padding=(8, 4),
            borderwidth=0,
        )
        style.map("Icon.TButton", background=[("active", theme.BUTTON_SECONDARY_HOVER)])

        style.configure(
            "Status.TLabel",
            background=theme.BG_STATUSBAR,
            foreground=theme.FG_STATUSBAR,
            font=theme.FONT_UI_SMALL,
        )
        style.configure(
            "Panel.TLabel",
            background=theme.BG_PANEL,
            foreground=theme.FG_MUTED,
            font=theme.FONT_UI_SMALL,
        )
        style.configure(
            "PanelTitle.TLabel",
            background=theme.BG_PANEL,
            foreground=theme.FG_EDITOR,
            font=theme.FONT_UI_BOLD,
        )
        style.configure(
            "Version.TLabel",
            background=theme.BG_PANEL,
            foreground=theme.FG_MUTED,
            font=theme.FONT_UI_SMALL,
        )

        # Notebook (tab strip) styling
        style.configure("TNotebook", background=theme.BG_PANEL, borderwidth=0, tabmargins=(6, 4, 0, 0))
        style.configure(
            "TNotebook.Tab",
            background=theme.BUTTON_SECONDARY_BG,
            foreground=theme.FG_MUTED,
            padding=(14, 7),
            font=theme.FONT_UI,
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", theme.BG_EDITOR)],
            foreground=[("selected", "#ffffff")],
        )

    # ------------------------------------------------------------------
    # Crash protection
    # ------------------------------------------------------------------
    def _install_crash_guard(self):
        """
        Catch any exception raised inside a Tk callback (button clicks,
        key bindings, timers, etc.) so a bug never takes down the whole
        application -- it is reported to the user and logged instead.
        """
        self.root.report_callback_exception = self._handle_uncaught_exception

    def _handle_uncaught_exception(self, exc_type, exc_value, exc_tb):
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(details, file=sys.__stderr__)
        try:
            self._append_console(f"\n[Unexpected Error]\n{details}\n", "stderr")
        except Exception:
            pass
        try:
            self._set_status("An unexpected error occurred (see Output)")
        except Exception:
            pass
        try:
            messagebox.showerror(
                "Unexpected Error",
                "Something went wrong, but Sotstech Python Editor will keep "
                f"running.\n\nDetails:\n{exc_value}",
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Workspace ("dosyam") helpers
    # ------------------------------------------------------------------
    def list_workspace_modules(self, exclude_path=None):
        """Return sorted base names (no .py) of every script in the workspace folder."""
        try:
            names = []
            exclude_abs = os.path.abspath(exclude_path) if exclude_path else None
            for fname in os.listdir(config.WORKSPACE_DIR):
                if not fname.endswith(".py"):
                    continue
                full_path = os.path.abspath(os.path.join(config.WORKSPACE_DIR, fname))
                if exclude_abs and full_path == exclude_abs:
                    continue
                names.append(fname[:-3])
            return sorted(names)
        except OSError:
            return []

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------
    def _build_menu_bar(self):
        menubar = tk.Menu(self.root, bg=theme.BG_TITLEBAR, fg=theme.FG_EDITOR,
                           activebackground=theme.ACCENT, activeforeground="#ffffff",
                           borderwidth=0)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, bg=theme.BG_PANEL, fg=theme.FG_EDITOR,
                             activebackground=theme.ACCENT, activeforeground="#ffffff")
        file_menu.add_command(label="New Tab", accelerator="Ctrl+T", command=lambda: self.new_tab())
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", accelerator="Ctrl+W", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0, bg=theme.BG_PANEL, fg=theme.FG_EDITOR,
                             activebackground=theme.ACCENT, activeforeground="#ffffff")
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z",
                               command=lambda: self._safe_edit_action("<<Undo>>"))
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y",
                               command=lambda: self._safe_edit_action("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X",
                               command=lambda: self._safe_edit_action("<<Cut>>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C",
                               command=lambda: self._safe_edit_action("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V",
                               command=lambda: self._safe_edit_action("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear Output", command=self.clear_console)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        run_menu = tk.Menu(menubar, tearoff=0, bg=theme.BG_PANEL, fg=theme.FG_EDITOR,
                            activebackground=theme.ACCENT, activeforeground="#ffffff")
        run_menu.add_command(label="Run Code", accelerator="F5", command=self.run_code)
        menubar.add_cascade(label="Run", menu=run_menu)

        ai_menu = tk.Menu(menubar, tearoff=0, bg=theme.BG_PANEL, fg=theme.FG_EDITOR,
                           activebackground=theme.ACCENT, activeforeground="#ffffff")
        ai_menu.add_command(label="AI Suggest for Selection", accelerator="Ctrl+Space",
                             command=self.request_ai_suggestion)
        ai_menu.add_separator()
        ai_menu.add_command(label="Add API Key", command=self.manage_api_key)
        menubar.add_cascade(label="AI Assistant", menu=ai_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=theme.BG_PANEL, fg=theme.FG_EDITOR,
                             activebackground=theme.ACCENT, activeforeground="#ffffff")
        help_menu.add_command(label=f"About {config.APP_NAME}", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def _safe_edit_action(self, virtual_event):
        try:
            self.active_tab().text.event_generate(virtual_event)
        except (tk.TclError, AttributeError):
            pass

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding=(theme.PAD_MD, theme.PAD_SM))
        toolbar.pack(side="top", fill="x")

        title_box = ttk.Frame(toolbar, style="Toolbar.TFrame")
        title_box.pack(side="left", padx=(theme.PAD_SM, theme.PAD_LG))
        ttk.Label(title_box, text=config.APP_DISPLAY_TITLE, style="PanelTitle.TLabel",
                  font=theme.FONT_TITLE).pack(side="top", anchor="w")
        ttk.Label(title_box, text=f"Version {config.APP_VERSION}", style="Version.TLabel").pack(
            side="top", anchor="w"
        )

        run_btn = ttk.Button(toolbar, text="\u25b6  Run", style="Accent.TButton", command=self.run_code)
        run_btn.pack(side="left", padx=(0, theme.PAD_SM))

        ai_btn = ttk.Button(toolbar, text="\u2726  AI Suggest", style="Secondary.TButton",
                             command=self.request_ai_suggestion)
        ai_btn.pack(side="left", padx=(0, theme.PAD_SM))

        api_btn = ttk.Button(toolbar, text="\U0001F511  Add API Key", style="Secondary.TButton",
                              command=self.manage_api_key)
        api_btn.pack(side="left", padx=(0, theme.PAD_SM))

        clear_btn = ttk.Button(toolbar, text="Clear Output", style="Secondary.TButton",
                                command=self.clear_console)
        clear_btn.pack(side="left")

    # ------------------------------------------------------------------
    # Main layout: tabbed editor on top, console output below
    # ------------------------------------------------------------------
    def _build_main_layout(self):
        paned = tk.PanedWindow(self.root, orient="vertical", sashwidth=6,
                                bg=theme.BORDER, bd=0, sashrelief="flat")
        paned.pack(side="top", fill="both", expand=True)

        # --- Editor panel (tab strip + "+" new-tab button) -----------------
        editor_container = tk.Frame(paned, bg=theme.BG_EDITOR)

        self.notebook = ttk.Notebook(editor_container)
        self.notebook.pack(side="top", fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Small floating "+ New Tab" control anchored to the top-right,
        # above the tab strip, for quickly opening additional pages.
        new_tab_btn = ttk.Button(editor_container, text="+ New Tab", style="Icon.TButton",
                                  command=lambda: self.new_tab())
        new_tab_btn.place(relx=1.0, y=2, anchor="ne")

        paned.add(editor_container, stretch="always", minsize=200)

        # --- Console / output panel ----------------------------------------
        console_container = tk.Frame(paned, bg=theme.BG_CONSOLE)
        console_header = ttk.Frame(console_container, style="TFrame", padding=(theme.PAD_MD, 4))
        console_header.pack(side="top", fill="x")
        ttk.Label(console_header, text="OUTPUT", style="Panel.TLabel").pack(side="left")

        console_body = tk.Frame(console_container, bg=theme.BG_CONSOLE)
        console_body.pack(side="top", fill="both", expand=True)

        self.console = tk.Text(
            console_body, bg=theme.BG_CONSOLE, fg=theme.FG_CONSOLE,
            font=theme.FONT_CONSOLE, state="disabled", wrap="word",
            borderwidth=0, highlightthickness=0, padx=8, pady=6,
        )
        console_scroll = ttk.Scrollbar(console_body, orient="vertical", command=self.console.yview)
        self.console.configure(yscrollcommand=console_scroll.set)
        console_scroll.pack(side="right", fill="y")
        self.console.pack(side="left", fill="both", expand=True)

        self.console.tag_configure("stdout", foreground=theme.FG_CONSOLE)
        self.console.tag_configure("stderr", foreground=theme.FG_CONSOLE_ERROR)
        self.console.tag_configure("success", foreground=theme.FG_CONSOLE_SUCCESS)

        paned.add(console_container, minsize=120)

    def _on_tab_changed(self, _event=None):
        self._update_cursor_status()
        self._update_title()

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------
    def new_tab(self, initial_text: str = "", file_path=None) -> EditorTab:
        tab = EditorTab(self.notebook, self, initial_text=initial_text, file_path=file_path)
        self.notebook.add(tab, text=tab.tab_label)
        self.notebook.select(tab)
        return tab

    def active_tab(self) -> EditorTab:
        current = self.notebook.select()
        return self.notebook.nametowidget(current)

    def _refresh_tab_title(self, tab: EditorTab):
        self.notebook.tab(tab, text=tab.tab_label)
        self._update_title()

    def close_current_tab(self):
        tab = self.active_tab()
        if tab.is_modified and not self._confirm_discard_changes(tab):
            return
        self.notebook.forget(tab)
        if not self.notebook.tabs():
            self.new_tab(initial_text=WELCOME_SNIPPET)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------
    def _build_status_bar(self):
        status_bar = ttk.Frame(self.root, style="Status.TFrame", padding=(theme.PAD_MD, 4))
        status_bar.pack(side="bottom", fill="x")

        self.status_message = tk.StringVar(value="Ready")
        self.status_cursor = tk.StringVar(value="Ln 1, Col 1")

        ttk.Label(status_bar, textvariable=self.status_message, style="Status.TLabel").pack(side="left")
        ttk.Label(status_bar, textvariable=self.status_cursor, style="Status.TLabel").pack(side="right")

    def _update_cursor_status(self):
        try:
            tab = self.active_tab()
        except (tk.TclError, AttributeError):
            return
        line, col = tab.text.index(tk.INSERT).split(".")
        self.status_cursor.set(f"Ln {line}, Col {int(col) + 1}")

    def _set_status(self, message: str):
        self.status_message.set(message)

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------
    def _bind_shortcuts(self):
        self.root.bind("<F5>", lambda e: self.run_code())
        self.root.bind("<Control-space>", lambda e: self.request_ai_suggestion())
        self.root.bind("<Control-t>", lambda e: self.new_tab())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_file_as())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------
    def open_file(self):
        path = filedialog.askopenfilename(
            initialdir=config.WORKSPACE_DIR,
            filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as exc:
            messagebox.showerror("Open File Failed", f"Could not open file:\n{exc}")
            return

        self.new_tab(initial_text=content, file_path=path)
        self._set_status(f"Opened {path}")

    def save_file(self):
        tab = self.active_tab()
        if tab.file_path is None:
            return self.save_file_as()
        self._write_to_path(tab, tab.file_path)

    def save_file_as(self):
        tab = self.active_tab()
        suggested_name = tab.display_name if tab.display_name.endswith(".py") else f"{tab.display_name}.py"
        path = filedialog.asksaveasfilename(
            initialdir=config.WORKSPACE_DIR,
            initialfile=suggested_name,
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        self._write_to_path(tab, path)

    def _write_to_path(self, tab: EditorTab, path: str):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(tab.get_code())
        except OSError as exc:
            messagebox.showerror("Save Failed", f"Could not save file:\n{exc}")
            return
        tab.mark_saved(path)
        self._set_status(f"Saved to {path}")

    def _confirm_discard_changes(self, tab: EditorTab) -> bool:
        if not tab.is_modified:
            return True
        answer = messagebox.askyesnocancel(
            "Unsaved Changes", f"'{tab.display_name}' has unsaved changes. Save before continuing?"
        )
        if answer is None:
            return False
        if answer:
            self.save_file()
        return True

    def _on_close(self):
        for tab_id in self.notebook.tabs():
            tab = self.notebook.nametowidget(tab_id)
            if tab.is_modified:
                self.notebook.select(tab)
                if not self._confirm_discard_changes(tab):
                    return
        self.root.destroy()

    def _update_title(self):
        try:
            tab = self.active_tab()
            name = tab.display_name
            marker = "\u25cf " if tab.is_modified else ""
        except (tk.TclError, AttributeError):
            name, marker = "Untitled", ""
        self.root.title(f"{marker}{name} \u2014 {config.APP_DISPLAY_TITLE}")

    # ------------------------------------------------------------------
    # Run code
    # ------------------------------------------------------------------

    # import name -> real pip package name, for the common cases where
    # they differ (e.g. "import cv2" needs "pip install opencv-python").
    _PIP_NAME_OVERRIDES = {
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "yaml": "PyYAML",
        "sklearn": "scikit-learn",
        "bs4": "beautifulsoup4",
        "Crypto": "pycryptodome",
        "serial": "pyserial",
        "dotenv": "python-dotenv",
        "dateutil": "python-dateutil",
        "docx": "python-docx",
        "pptx": "python-pptx",
    }

    def _pip_package_name(self, module_name: str) -> str:
        root = module_name.split(".")[0]
        return self._PIP_NAME_OVERRIDES.get(root, root)

    def _pip_base_command(self):
        """Return the base command list used to invoke pip, or None if no
        usable Python/pip could be found (this can happen inside a
        PyInstaller-built .exe, which has no pip of its own)."""
        if not getattr(sys, "frozen", False):
            return [sys.executable, "-m", "pip"]
        import shutil
        for candidate in ("python", "python3", "py"):
            found = shutil.which(candidate)
            if found:
                return [found, "-m", "pip"]
        return None

    def _ensure_external_packages_on_path(self):
        """A frozen .exe runs with its own bundled interpreter and has NO
        access to packages installed in a normal system Python (e.g. the
        one 'python' on PATH points to) -- not even ones that are already
        installed there. So pip can report "already satisfied" while the
        running .exe still can't import it. Fix: find that system Python
        once per session and add its site-packages *and* standard-library
        folders to our sys.path so those modules become importable here
        too. The standard-library folders matter because PyInstaller only
        bundles the stdlib modules it can see being used when the app is
        built -- a module the user's own code imports at run time (e.g.
        "import pdb") may simply be missing from the .exe even though it
        ships with every normal Python install. Those can never be
        installed via pip (they're not on PyPI), so making them
        importable this way is the fix, not a pip install attempt."""
        if not getattr(sys, "frozen", False):
            return  # running as plain "python main.py": nothing special needed
        if getattr(self, "_external_paths_ready", False):
            return
        self._external_paths_ready = True  # only probe once per session
        pip_cmd = self._pip_base_command()
        if pip_cmd is None:
            return
        python_exe = pip_cmd[0]
        probe = (
            "import site, sysconfig;"
            "paths=set(site.getsitepackages());"
            "paths.add(site.getusersitepackages());"
            "paths.add(sysconfig.get_path('stdlib'));"
            "paths.add(sysconfig.get_path('platstdlib'));"
            "print(chr(10).join(p for p in paths if p))"
        )
        try:
            result = subprocess.run(
                [python_exe, "-c", probe],
                capture_output=True, text=True, timeout=15,
            )
        except Exception:  # noqa: BLE001 - best-effort only
            return
        if result.returncode != 0:
            return
        found_paths = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and line not in sys.path:
                sys.path.append(line)
            if line:
                found_paths.append(line)
        importlib.invalidate_caches()
        self._external_site_paths = found_paths
        self._register_dll_search_paths(found_paths)

        # sys.path only helps with modules that haven't been imported
        # yet. A package the app itself already imports -- tkinter, most
        # notably -- is loaded straight from the frozen bundle, and
        # PyInstaller only bundled the submodules it saw referenced
        # somewhere in this app's own source (ttk, filedialog,
        # messagebox). A submodule user code asks for later, like
        # "tkinter.font" or "tkinter.simpledialog", isn't found by
        # sys.path at all in that case: Python resolves it by searching
        # the *parent package's* __path__, not sys.path. So extend the
        # __path__ of every already-loaded top-level package with the
        # matching real folder from the system Python, when one exists.
        for name, mod in list(sys.modules.items()):
            if mod is None or "." in name:
                continue
            mod_path = getattr(mod, "__path__", None)
            if mod_path is None:
                continue
            for base in found_paths:
                candidate = os.path.join(base, name)
                if os.path.isdir(candidate) and candidate not in mod_path:
                    try:
                        mod_path.append(candidate)
                    except Exception:  # noqa: BLE001 - best-effort only
                        pass

    def _register_dll_search_paths(self, paths):
        """Windows-only. Since Python 3.8, the OS loader no longer
        searches PATH or the current directory for a compiled extension
        module's own DLL dependencies -- each directory has to be
        registered explicitly with os.add_dll_directory(). Packages like
        numpy and opencv-python ship their bundled runtime DLLs in a
        sibling "<distname>.libs" folder next to the package itself
        (the convention used by the 'delvewheel' tool that repairs their
        Windows wheels); that folder is normally registered by the
        package's own __init__.py the first time it's imported, but
        registering it ourselves too is a harmless, cheap safety net --
        and the actual fix when that doesn't happen for some reason,
        which is the classic cause of a "DLL load failed: the specified
        module could not be found" error that survives a clean
        reinstall. Safe to call repeatedly; call again after any fresh
        pip install/reinstall so a just-created ".libs" folder gets
        picked up too."""
        if os.name != "nt":
            return
        add_dll_directory = getattr(os, "add_dll_directory", None)
        if add_dll_directory is None:
            return
        for base in paths:
            try:
                add_dll_directory(base)
            except OSError:
                pass
            try:
                entries = os.listdir(base)
            except OSError:
                continue
            for entry in entries:
                if entry.endswith(".libs"):
                    libs_dir = os.path.join(base, entry)
                    if os.path.isdir(libs_dir):
                        try:
                            add_dll_directory(libs_dir)
                        except OSError:
                            pass

    def _ensure_matplotlib_gui_backend(self):
        """If matplotlib is available, force it onto the 'TkAgg' backend
        (the app is already a Tkinter app, so this is always the right
        choice) before user code runs. Without this, matplotlib's own
        automatic backend probing can silently fall back to 'Agg' --
        a headless, image-only backend -- especially inside a frozen
        .exe, which is why plt.show() then does nothing but print a
        'non-GUI backend, so cannot show the figure' warning instead of
        opening a window.

        This is only a convenience pass -- it must never be allowed to
        crash run_code itself. A broken/incompatible matplotlib install
        (for example, one left stale by a NumPy major-version upgrade)
        can fail with all sorts of exceptions while merely being
        imported (AttributeError, RuntimeError, ...), not just
        ImportError, so every step here is guarded broadly. If this
        fails, run_code simply proceeds to run the user's code as-is;
        if that code needs matplotlib too, the failure surfaces there
        instead, where _exec_with_auto_install can actually try to fix
        it (see _looks_like_numpy_abi_mismatch)."""
        try:
            import matplotlib
        except Exception as exc:  # noqa: BLE001 - see docstring
            if not isinstance(exc, ImportError):
                self._append_console(
                    f"\n[Warning] matplotlib is installed but failed to load "
                    f"({exc}). Continuing without forcing a GUI backend; if "
                    f"your code needs matplotlib, the error will show up "
                    f"there.\n",
                    "stderr",
                )
            return  # not installed yet -- the normal auto-install flow handles it
        try:
            matplotlib.use("TkAgg", force=True)
        except Exception:
            return
        # If a previous Run already imported pyplot (baking in whatever
        # backend it auto-selected then), switch that live instance too --
        # matplotlib.use() alone has no effect once pyplot is loaded.
        plt_module = sys.modules.get("matplotlib.pyplot")
        if plt_module is not None:
            try:
                plt_module.switch_backend("TkAgg")
            except Exception:
                pass

    def run_code(self):
        tab = self.active_tab()
        code = tab.get_code().strip()
        if not code:
            messagebox.showwarning("Nothing to Run", "Please write some code first.")
            return

        self.clear_console()
        self._set_status(f"Running {tab.display_name}\u2026")

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = ConsoleRedirector(self.console, tag="stdout")
        sys.stderr = ConsoleRedirector(self.console, tag="stderr")

        # Let code being run "import" or "from ... import" any other .py
        # file that lives in the "dosyam" workspace folder (e.g. a file
        # named processing.py saved alongside main.py's tab).
        workspace_dir = config.WORKSPACE_DIR
        path_added = workspace_dir not in sys.path
        if path_added:
            sys.path.insert(0, workspace_dir)

        # When running as a built .exe, make sure packages already
        # installed on the system's own Python are visible too.
        self._ensure_external_packages_on_path()
        self._ensure_matplotlib_gui_backend()

        try:
            self._exec_with_auto_install(code, already_tried=set())
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            if path_added:
                try:
                    sys.path.remove(workspace_dir)
                except ValueError:
                    pass

    def _exec_with_auto_install(self, code, already_tried):
        """Run code; if it fails because a third-party library isn't
        installed (or is installed but broken/incompatible, e.g. a
        Windows 'DLL load failed' error from a compiled package), install
        or reinstall it automatically (printing progress to the console)
        and retry, instead of just failing with an import error."""
        exec_globals = {"__name__": "__main__", "input": self._gui_input}

        force_reinstall = False
        reinstall_reason = None  # "dll" or "numpy_abi", set alongside force_reinstall

        try:
            exec(code, exec_globals)
            self._append_console("\n[Process finished successfully]\n", "success")
            self._set_status("Run completed successfully")
            return
        except ModuleNotFoundError as exc:
            module_name = exc.name or ""
            root_module = module_name.split(".")[0]
            if root_module in getattr(sys, "stdlib_module_names", ()):
                # Standard-library modules are never on PyPI, so pip can
                # never install them -- if one is still missing here it's
                # because this .exe build didn't bundle it. Re-probe the
                # system Python's stdlib path once (in case it wasn't
                # found on the first try, e.g. Python was just installed)
                # and retry; if it's still missing, say so plainly instead
                # of attempting (and failing) a pip install.
                token = f"stdlib:{root_module}"
                if token not in already_tried:
                    already_tried.add(token)
                    self._append_console(
                        f"\n[Info] '{module_name}' is a Python standard-library "
                        f"module missing from this build. Looking for it in the "
                        f"system Python installation...\n",
                        "stdout",
                    )
                    self.root.update_idletasks()
                    self._external_paths_ready = False
                    self._ensure_external_packages_on_path()
                    importlib.invalidate_caches()
                    self._exec_with_auto_install(code, already_tried)
                    return
                self._append_console(
                    f"\n[Error] '{module_name}' is a standard-library module and "
                    f"can't be installed with pip. It could not be found in the "
                    f"system Python either -- make sure Python is installed and "
                    f"added to PATH, then try Run again.\n",
                    "stderr",
                )
                self._set_status("Run finished with an error")
                return
            package = self._pip_package_name(module_name)
        except ImportError as exc:
            # The module exists on disk but failed to *load* -- most
            # commonly a Windows "DLL load failed while importing X: The
            # specified module could not be found" error from a compiled
            # (C-extension) package. A plain "pip install" would just
            # report "already satisfied" and change nothing here, since
            # pip sees it as already there; what actually fixes this most
            # of the time is a clean *reinstall* (ignoring any cached or
            # partially-broken copy), so that's what gets attempted.
            module_name = exc.name or self._guess_module_from_import_error(str(exc))
            if not module_name:
                self._append_console(f"\n[Error] {exc}\n", "stderr")
                self._set_status("Run finished with an error")
                return
            package = self._pip_package_name(module_name)
            force_reinstall = True
            reinstall_reason = "dll"
            if self._looks_like_numpy_abi_mismatch(exc):
                # A module (matplotlib, scipy, pandas, ...) was compiled
                # against a different NumPy major version than the one
                # currently installed -- typically because installing or
                # reinstalling some other package (like opencv-python,
                # which requires numpy>=2) just upgraded NumPy underneath
                # it. NumPy itself isn't what's broken; the *other*
                # package's compiled extension is stale relative to it.
                # Find which package that is from the traceback and
                # reinstall that one so its extension gets rebuilt/
                # refetched to match the NumPy that's now installed.
                broken_package = self._guess_broken_package_from_traceback(exc)
                if broken_package:
                    module_name = broken_package
                    package = self._pip_package_name(broken_package)
                    force_reinstall = True
                    reinstall_reason = "numpy_abi"
                else:
                    self._append_console(
                        f"\n[Error] {exc}\n"
                        f"[Info] This looks like a NumPy version mismatch "
                        f"(some package's compiled extension is stale "
                        f"relative to the NumPy version now installed), but "
                        f"the affected package couldn't be identified "
                        f"automatically. Reinstalling it manually should fix "
                        f"this.\n",
                        "stderr",
                    )
                    self._set_status("Run finished with an error")
                    return
            else:
                self._append_console(f"\n[Error] {exc}\n", "stderr")
                self._set_status("Run finished with an error")
                return

        token = f"reinstall:{package}" if force_reinstall else f"install:{package}"
        if token in already_tried:
            if reinstall_reason == "numpy_abi":
                self._append_console(
                    f"\n[Error] Reinstalling '{package}' didn't fix the NumPy "
                    f"version mismatch. This usually means '{package}' doesn't "
                    f"have a release on PyPI yet that supports the currently "
                    f"installed NumPy version. Try either downgrading NumPy "
                    f"(pip install \"numpy<2\") or checking for a newer version "
                    f"of '{package}'.\n",
                    "stderr",
                )
            elif force_reinstall:
                self._append_console(
                    f"\n[Error] Reinstalling '{package}' didn't fix loading "
                    f"'{module_name}'. A DLL load failure that survives a clean "
                    f"reinstall is usually an environment issue pip can't fix on "
                    f"its own -- commonly a missing Microsoft Visual C++ "
                    f"Redistributable, or a 32-bit/64-bit mismatch between "
                    f"Python and the package. Check those on the system that's "
                    f"running this.\n",
                    "stderr",
                )
            else:
                self._append_console(
                    f"\n[Error] '{package}' installed but '{module_name}' is still "
                    f"not found. It may need a different package name.\n",
                    "stderr",
                )
            self._set_status("Run finished with an error")
            return

        pip_cmd = self._pip_base_command()
        if pip_cmd is None:
            self._append_console(
                f"\n[Error] Module '{module_name}' is not usable, and no "
                f"Python/pip could be found to fix it automatically. Please "
                f"{'reinstall' if force_reinstall else 'install'} '{package}' "
                f"manually (pip install {'--force-reinstall --no-cache-dir ' if force_reinstall else ''}{package}).\n",
                "stderr",
            )
            self._set_status("Run finished with an error")
            return

        if force_reinstall:
            self._append_console(
                f"\n[Info] '{module_name}' failed to load (DLL load failed). "
                f"Reinstalling '{package}' from scratch...\n",
                "stdout",
            )
            install_args = ["install", "--force-reinstall", "--no-cache-dir", package]
        else:
            self._append_console(
                f"\n[Info] Module '{module_name}' not found. Installing "
                f"'{package}'...\n",
                "stdout",
            )
            install_args = ["install", package]
        self.root.update_idletasks()

        try:
            result = subprocess.run(
                pip_cmd + install_args,
                capture_output=True,
                text=True,
            )
        except Exception as install_exc:  # noqa: BLE001
            self._append_console(f"[Error] Install failed: {install_exc}\n", "stderr")
            self._set_status("Run finished with an error")
            return

        if result.stdout:
            self._append_console(result.stdout, "stdout")
        if result.returncode != 0:
            if result.stderr:
                self._append_console(result.stderr, "stderr")
            self._append_console(f"[Error] Could not install '{package}'.\n", "stderr")
            self._set_status("Run finished with an error")
            return

        verb = "reinstalled" if force_reinstall else "installed"
        self._append_console(f"[Info] '{package}' {verb}. Re-running...\n", "success")
        importlib.invalidate_caches()
        # A fresh install can create a new sibling "<name>.libs" DLL
        # folder (see _register_dll_search_paths) that didn't exist
        # during the one-time path probe -- register it now too.
        self._register_dll_search_paths(getattr(self, "_external_site_paths", []))
        already_tried.add(token)
        self._exec_with_auto_install(code, already_tried)

    @staticmethod
    def _guess_module_from_import_error(message: str):
        """Best-effort fallback for the rare ImportError that doesn't set
        .name (e.g. some DLL-load-failure messages): pull the module name
        out of '... while importing <name>: ...' or '... importing <name>'."""
        import re
        match = re.search(r"importing\s+([\w.]+)", message)
        return match.group(1) if match else ""

    @staticmethod
    def _looks_like_numpy_abi_mismatch(exc) -> bool:
        """True for the classic 'this module was compiled against a
        different NumPy major version' family of errors -- e.g.
        'AttributeError: _ARRAY_API not found', or
        'ImportError: numpy.core.multiarray failed to import'. These show
        up when some *other* already-installed package's compiled
        extension is stale relative to whatever NumPy version is
        currently installed (most often right after NumPy itself just
        got upgraded as a side effect of installing/reinstalling a
        different package)."""
        text = f"{type(exc).__name__}: {exc}".lower()
        markers = (
            "_array_api not found",
            "multiarray failed to import",
            "compiled using numpy 1.x",
            "compiled against numpy",
            "numpy 1.x cannot be run in",
            "numpy.dtype size changed",
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _guess_broken_package_from_traceback(exc):
        """Walk the exception's traceback and return the name of the
        deepest third-party package involved (i.e. the last frame whose
        file lives under a 'site-packages' folder) -- that's the package
        whose compiled extension actually failed, which is what needs
        reinstalling. NumPy itself is skipped: in this error family NumPy
        is the version everything else must catch up to, not the broken
        part, so reinstalling NumPy again would just restore the same
        situation."""
        import re
        import traceback as tb_module
        for frame in reversed(tb_module.extract_tb(exc.__traceback__)):
            match = re.search(r"site-packages[\\/]+([A-Za-z0-9_.\-]+)", frame.filename)
            if not match:
                continue
            name = match.group(1)
            if name.endswith(".py"):
                name = name[:-3]
            root = name.split(".")[0]
            if root and root.lower() != "numpy":
                return root
        return None


    def _append_console(self, text: str, tag: str):
        self.console.configure(state="normal")
        self.console.insert(tk.END, text, tag)
        self.console.see(tk.END)
        self.console.configure(state="disabled")

    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.configure(state="disabled")

    # ------------------------------------------------------------------
    # input() support for executed code
    # ------------------------------------------------------------------
    def _gui_input(self, prompt: str = "") -> str:
        """
        Drop-in replacement for the built-in input(), used while running
        code in the editor. Shows the prompt in the Output panel and
        opens a small dialog to collect the value, so calling input() in
        the user's code never hangs or errors out.
        """
        prompt_text = str(prompt)
        if prompt_text:
            self._append_console(prompt_text, "stdout")

        value = self._ask_input_dialog(prompt_text)
        if value is None:
            raise EOFError("Input was cancelled.")

        self._append_console(value + "\n", "stdout")
        return value

    def _ask_input_dialog(self, prompt: str):
        result = {"value": None}

        dialog = tk.Toplevel(self.root)
        dialog.title("Input Required")
        dialog.configure(bg=theme.BG_PANEL)
        dialog.geometry("440x180")
        dialog.transient(self.root)
        dialog.grab_set()

        header = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        header.pack(side="top", fill="x")
        ttk.Label(header, text="This program is asking for input:", style="PanelTitle.TLabel",
                  font=theme.FONT_UI_BOLD).pack(anchor="w")
        if prompt.strip():
            ttk.Label(header, text=prompt.strip(), style="Panel.TLabel",
                      wraplength=400, justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(dialog, bg=theme.BG_PANEL)
        body.pack(side="top", fill="x", padx=theme.PAD_MD, pady=theme.PAD_MD)
        value_var = tk.StringVar()
        entry = ttk.Entry(body, textvariable=value_var, font=theme.FONT_UI)
        entry.pack(fill="x")
        entry.focus_set()

        footer = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        footer.pack(side="bottom", fill="x")

        def submit(_event=None):
            result["value"] = value_var.get()
            dialog.destroy()

        def cancel():
            result["value"] = None
            dialog.destroy()

        ttk.Button(footer, text="Submit", style="Accent.TButton", command=submit).pack(side="right")
        ttk.Button(footer, text="Cancel", style="Secondary.TButton", command=cancel).pack(
            side="right", padx=(0, theme.PAD_SM)
        )
        dialog.bind("<Return>", submit)
        dialog.protocol("WM_DELETE_WINDOW", cancel)

        # Blocks only this dialog while still pumping the Tk event loop,
        # so the rest of the app stays responsive until the user answers.
        dialog.wait_window()
        return result["value"]

    # ------------------------------------------------------------------
    # AI Assistant: select code -> describe what you want -> review -> apply
    # ------------------------------------------------------------------
    def request_ai_suggestion(self):
        tab = self.active_tab()
        try:
            sel_start = tab.text.index(tk.SEL_FIRST)
            sel_end = tab.text.index(tk.SEL_LAST)
            selected_code = tab.text.get(sel_start, sel_end)
        except tk.TclError:
            messagebox.showwarning(
                "No Selection",
                "Please select the code you want the AI to work on first, "
                "then click AI Suggest again.",
            )
            return

        if not selected_code.strip():
            messagebox.showwarning("No Selection", "Please select the code you want the AI to work on first.")
            return

        self._show_instruction_dialog(tab, selected_code, sel_start, sel_end)

    def _show_instruction_dialog(self, tab: EditorTab, selected_code: str, sel_start: str, sel_end: str):
        dialog = tk.Toplevel(self.root)
        dialog.title("AI Suggest")
        dialog.configure(bg=theme.BG_PANEL)
        dialog.geometry("560x360")
        dialog.transient(self.root)
        dialog.grab_set()

        header = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        header.pack(side="top", fill="x")
        ttk.Label(header, text="What should the AI do with the selected code?",
                  style="PanelTitle.TLabel", font=theme.FONT_UI_BOLD,
                  wraplength=520, justify="left").pack(anchor="w")
        ttk.Label(
            header,
            text='e.g. "Optimize this for performance", "Add error handling", '
                 '"Add docstrings and comments", "Fix the bug in this function"',
            style="Panel.TLabel", wraplength=520, justify="left",
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(dialog, bg=theme.BG_PANEL)
        body.pack(side="top", fill="both", expand=True, padx=theme.PAD_MD, pady=theme.PAD_MD)

        instruction_text = tk.Text(
            body, bg=theme.BG_EDITOR, fg=theme.FG_EDITOR, insertbackground="#ffffff",
            font=theme.FONT_UI, height=5, wrap="word", borderwidth=1,
            highlightthickness=1, highlightbackground=theme.BORDER, padx=8, pady=8,
        )
        instruction_text.pack(fill="both", expand=True)
        instruction_text.focus_set()

        preview_label = ttk.Label(
            body, text=f"Selected: {len(selected_code.splitlines()) or 1} line(s) of code",
            style="Panel.TLabel",
        )
        preview_label.pack(anchor="w", pady=(theme.PAD_SM, 0))

        footer = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        footer.pack(side="bottom", fill="x")

        def on_generate():
            instruction = instruction_text.get("1.0", "end-1c").strip()
            dialog.destroy()
            self._run_ai_request(tab, selected_code, instruction, sel_start, sel_end)

        ttk.Button(footer, text="Generate Suggestion", style="Accent.TButton",
                   command=on_generate).pack(side="right")
        ttk.Button(footer, text="Cancel", style="Secondary.TButton",
                   command=dialog.destroy).pack(side="right", padx=(0, theme.PAD_SM))

        dialog.bind("<Return>", lambda e: on_generate())

    def _run_ai_request(self, tab: EditorTab, selected_code: str, instruction: str,
                         sel_start: str, sel_end: str):
        self._set_status("Requesting AI suggestion\u2026")
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        try:
            suggestion = self.ai_assistant.get_suggestion(selected_code, instruction)
        except AIAssistantError as exc:
            self._set_status("AI request failed")
            messagebox.showerror("AI Assistant", str(exc))
            return
        finally:
            self.root.config(cursor="")

        self._set_status("AI suggestion ready")
        self._show_suggestion_dialog(tab, suggestion, sel_start, sel_end)

    def _show_suggestion_dialog(self, tab: EditorTab, suggestion, sel_start: str, sel_end: str):
        dialog = tk.Toplevel(self.root)
        dialog.title("AI Suggestion")
        dialog.configure(bg=theme.BG_PANEL)
        dialog.geometry("760x560")
        dialog.transient(self.root)
        dialog.grab_set()

        header = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        header.pack(side="top", fill="x")
        ttk.Label(header, text="AI Suggested Code", style="PanelTitle.TLabel",
                  font=theme.FONT_TITLE).pack(side="top", anchor="w")
        ttk.Label(header, text=f'Instruction: "{suggestion.instruction}"', style="Panel.TLabel",
                  wraplength=700, justify="left").pack(side="top", anchor="w", pady=(2, 0))

        body = tk.Frame(dialog, bg=theme.BG_PANEL)
        body.pack(side="top", fill="both", expand=True, padx=theme.PAD_MD, pady=(0, theme.PAD_MD))

        from syntax_highlighter import SyntaxHighlighter  # local import avoids a cycle at module load

        text_widget = tk.Text(
            body, bg=theme.BG_EDITOR, fg=theme.FG_EDITOR, insertbackground="#ffffff",
            font=theme.FONT_EDITOR, wrap="none", borderwidth=0, highlightthickness=0,
            padx=8, pady=6,
        )
        scroll = ttk.Scrollbar(body, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)
        text_widget.insert("1.0", suggestion.suggested_code)

        dialog_highlighter = SyntaxHighlighter(text_widget)
        dialog_highlighter.highlight()

        footer = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        footer.pack(side="bottom", fill="x")
        ttk.Label(footer, text="Do you want to replace the selected code with this suggestion?",
                  style="Panel.TLabel").pack(side="left")

        def apply_and_close():
            try:
                tab.text.delete(sel_start, sel_end)
                tab.text.insert(sel_start, text_widget.get("1.0", "end-1c"))
            except tk.TclError:
                # Selection indices are no longer valid (e.g. text changed) --
                # fall back to inserting at the current cursor position.
                tab.text.insert(tk.INSERT, text_widget.get("1.0", "end-1c"))
            tab.highlighter.highlight()
            tab.line_numbers.redraw()
            self._set_status("AI suggestion applied")
            dialog.destroy()

        ttk.Button(footer, text="Yes, Replace Code", style="Accent.TButton",
                   command=apply_and_close).pack(side="right")
        ttk.Button(footer, text="No, Keep Original", style="Secondary.TButton",
                   command=dialog.destroy).pack(side="right", padx=(0, theme.PAD_SM))

    # ------------------------------------------------------------------
    # API key management (set once, stored locally, editable anytime)
    # ------------------------------------------------------------------
    def manage_api_key(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add API Key")
        dialog.configure(bg=theme.BG_PANEL)
        dialog.geometry("480x260")
        dialog.transient(self.root)
        dialog.grab_set()

        header = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        header.pack(side="top", fill="x")
        ttk.Label(header, text="OpenAI API Key", style="PanelTitle.TLabel",
                  font=theme.FONT_UI_BOLD).pack(anchor="w")

        current_key = config.OPENAI_API_KEY
        status_text = (
            f"Currently saved key ends in \u2026{current_key[-4:]}" if current_key
            else "No API key has been saved yet."
        )
        ttk.Label(header, text=status_text, style="Panel.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Label(
            header,
            text="You only need to set this once. You can come back here anytime to change it.",
            style="Panel.TLabel", wraplength=440, justify="left",
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(dialog, bg=theme.BG_PANEL)
        body.pack(side="top", fill="x", padx=theme.PAD_MD, pady=theme.PAD_MD)

        key_var = tk.StringVar()
        entry = ttk.Entry(body, textvariable=key_var, show="\u2022", font=theme.FONT_UI, width=48)
        entry.pack(fill="x")
        entry.focus_set()

        footer = ttk.Frame(dialog, style="TFrame", padding=theme.PAD_MD)
        footer.pack(side="bottom", fill="x")

        def on_save():
            new_key = key_var.get().strip()
            if not new_key:
                messagebox.showwarning("Add API Key", "Please paste a valid API key first.")
                return
            config.OPENAI_API_KEY = new_key
            config.save_api_key(new_key)
            self.ai_assistant.reset_client()
            self._set_status("API key saved")
            messagebox.showinfo(
                "API Key Saved",
                "Your OpenAI API key has been saved on this computer.\n"
                "You will not be asked again -- come back to this dialog "
                "anytime you want to change it.",
            )
            dialog.destroy()

        def on_clear():
            config.OPENAI_API_KEY = ""
            config.clear_saved_api_key()
            self.ai_assistant.reset_client()
            self._set_status("API key removed")
            dialog.destroy()

        ttk.Button(footer, text="Save Key", style="Accent.TButton", command=on_save).pack(side="right")
        ttk.Button(footer, text="Cancel", style="Secondary.TButton",
                   command=dialog.destroy).pack(side="right", padx=(0, theme.PAD_SM))
        if current_key:
            ttk.Button(footer, text="Remove Saved Key", style="Secondary.TButton",
                       command=on_clear).pack(side="left")

        dialog.bind("<Return>", lambda e: on_save())

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------
    def show_about(self):
        messagebox.showinfo(
            f"About {config.APP_NAME}",
            f"{config.APP_DISPLAY_TITLE}\nVersion {config.APP_VERSION}\n\n"
            "A professional, multi-tab, AI-assisted Python code editor.\n"
            "Write code across multiple tabs, run it instantly, and get "
            "AI-powered suggestions for any selection based on your own "
            "instructions.",
        )