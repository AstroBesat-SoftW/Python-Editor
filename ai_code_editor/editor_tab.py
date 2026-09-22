"""
editor_tab.py
--------------
Represents a single editor page/tab: its own Text widget, line-number
gutter, syntax highlighter, and file state (path + modified flag). The
main application can host any number of these inside a ttk.Notebook,
giving the editor multi-page support.

It also implements a lightweight "ghost text" import auto-suggestion:
while typing "from " or "import " it offers the name of another .py
file found in the workspace folder, shown in faded grey right after
the cursor. Press Tab to accept it, or keep typing anything else and
it disappears.
"""

import os
import re
import tkinter as tk
from tkinter import ttk
from typing import Optional

import theme
from line_numbers import LineNumbers
from syntax_highlighter import SyntaxHighlighter

GHOST_TAG = "ghost_suggestion"

# Matches a line, up to the cursor, that is exactly "from " or "import "
# optionally followed by a partially-typed module name -- nothing else.
_IMPORT_PATTERN = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)?$")


class EditorTab(tk.Frame):
    _untitled_counter = 0

    def __init__(self, master, app, initial_text: str = "", file_path: Optional[str] = None):
        super().__init__(master, bg=theme.BG_EDITOR)
        self.app = app
        self.file_path = file_path
        self.is_modified = False

        if file_path is None:
            EditorTab._untitled_counter += 1
            self._untitled_id = EditorTab._untitled_counter
        else:
            self._untitled_id = None

        self.text = tk.Text(
            self, bg=theme.BG_EDITOR, fg=theme.FG_EDITOR,
            insertbackground="#ffffff", selectbackground=theme.ACCENT,
            font=theme.FONT_EDITOR, undo=True, wrap="none",
            borderwidth=0, highlightthickness=0, padx=8, pady=6,
        )
        self.text.tag_configure(GHOST_TAG, foreground=theme.FG_MUTED)

        self.line_numbers = LineNumbers(self, self.text)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._on_scroll)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.line_numbers.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.highlighter = SyntaxHighlighter(self.text)
        self.text.bind("<KeyRelease>", self._on_change)
        self.text.bind("<<Modified>>", self._on_modified_flag)
        self.text.bind("<ButtonRelease-1>", lambda e: self.app._update_cursor_status())
        self.text.bind("<Tab>", self._on_tab_key)
        self.text.bind("<Escape>", lambda e: self._clear_ghost())
        self.text.bind("<Button-1>", lambda e: self._clear_ghost())
        self.text.bind("<FocusOut>", lambda e: self._clear_ghost())

        if initial_text:
            self.text.insert("1.0", initial_text)
        self.text.edit_modified(False)
        self.highlighter.highlight()
        self.line_numbers.redraw()

    # ------------------------------------------------------------------
    def _on_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.redraw()

    def _on_change(self, _event=None):
        self.line_numbers.redraw()
        self.highlighter.schedule_highlight()
        self.app._update_cursor_status()
        self._update_import_suggestion()

    def _on_modified_flag(self, _event=None):
        if self.text.edit_modified():
            self.is_modified = True
            self.app._refresh_tab_title(self)
            self.text.edit_modified(False)

    # ------------------------------------------------------------------
    # Import auto-suggestion ("ghost text")
    # ------------------------------------------------------------------
    def _has_ghost(self) -> bool:
        return bool(self.text.tag_ranges(GHOST_TAG))

    def _clear_ghost(self):
        ranges = self.text.tag_ranges(GHOST_TAG)
        if ranges:
            self.text.delete(ranges[0], ranges[1])

    def _accept_ghost(self):
        ranges = self.text.tag_ranges(GHOST_TAG)
        if not ranges:
            return
        start, end = ranges[0], ranges[1]
        self.text.tag_remove(GHOST_TAG, start, end)
        self.text.mark_set(tk.INSERT, end)

    def _on_tab_key(self, _event):
        if self._has_ghost():
            self._accept_ghost()
            return "break"
        self.text.insert(tk.INSERT, "    ")
        return "break"

    def _update_import_suggestion(self):
        try:
            self._clear_ghost()
            line_text = self.text.get("insert linestart", "insert")
            match = _IMPORT_PATTERN.match(line_text)
            if not match:
                return

            partial = match.group(1) or ""
            candidates = self.app.list_workspace_modules(exclude_path=self.file_path)
            best = next(
                (name for name in candidates if name.startswith(partial) and name != partial),
                None,
            )
            if best is None:
                return

            remainder = best[len(partial):]
            if not remainder:
                return

            insert_index = self.text.index(tk.INSERT)
            self.text.insert(insert_index, remainder, GHOST_TAG)
            self.text.mark_set(tk.INSERT, insert_index)
        except (tk.TclError, re.error):
            # Never let the suggestion feature disrupt typing.
            pass

    # ------------------------------------------------------------------
    @property
    def display_name(self) -> str:
        if self.file_path:
            return os.path.basename(self.file_path)
        return f"Untitled-{self._untitled_id}"

    @property
    def tab_label(self) -> str:
        marker = "\u25cf " if self.is_modified else ""
        return f"{marker}{self.display_name}"

    def get_code(self) -> str:
        self._clear_ghost()
        return self.text.get("1.0", "end-1c")

    def mark_saved(self, file_path: str):
        self.file_path = file_path
        self.is_modified = False
        self.app._refresh_tab_title(self)
