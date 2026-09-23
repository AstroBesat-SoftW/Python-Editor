import os
import re
import sys
import json
import keyword
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# =============================================================================
# config.py
# =============================================================================

class config:
    APP_NAME = "Sotstech AI Editor"
    APP_DISPLAY_TITLE = "Sotstech AI Python Editor"
    APP_VERSION = "3.3.0"

    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    AI_MAX_TOKENS = 2500
    AI_TEMPERATURE = 0.4

    DEFAULT_WINDOW_SIZE = "1350x800"
    MIN_WINDOW_SIZE = (1000, 640)

    if getattr(sys, "frozen", False):
        APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    else:
        APP_DIR = os.path.dirname(os.path.abspath(__file__))
    WORKSPACE_DIR = os.path.join(APP_DIR, "dosyam")
    ASSETS_DIR = os.path.join(APP_DIR, "assets")
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    _SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".sotstech_python_editor")
    _SETTINGS_FILE = os.path.join(_SETTINGS_DIR, "settings.json")

    @staticmethod
    def _read_settings() -> dict:
        try:
            with open(config._SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _write_settings(data: dict) -> None:
        os.makedirs(config._SETTINGS_DIR, exist_ok=True)
        with open(config._SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_saved_api_key() -> str:
        return config._read_settings().get("openai_api_key", "")

    @staticmethod
    def save_api_key(key: str) -> None:
        data = config._read_settings()
        data["openai_api_key"] = key.strip()
        config._write_settings(data)


config.OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "") or config.load_saved_api_key()

# =============================================================================
# TEMA GÜNCELLEMESİ (Görseldeki canlı renkler ve lacivert tonlarına uyarlandı)
# =============================================================================
class theme:
    BG_APP = "#080b14"             # En dış arka plan
    BG_PANEL = "#0f1423"           # Yan panel ve iç pencereler
    BG_EDITOR = "#0b0f19"          # Editör arka planı
    BG_EDITOR_GUTTER = "#0b0f19"   # Satır numaraları arka planı
    BG_CONSOLE = "#080b14"         # Terminal arka planı
    BG_TITLEBAR = "#080b14"        # Üst bar
    BG_RAIL = "#080b14"            # En sol menü şeridi
    BG_INPUT = "#1a2238"           # Chat input
    BG_BUBBLE_USER = "#1f2b47"     # Kullanıcı mesaj balonu
    BG_BUBBLE_AI = "#0f1423"       # AI mesaj balonu
    BG_TAB_ACTIVE = "#161f38"      # Aktif sekme
    BG_TAB_IDLE = "#0f1423"        # Pasif sekme

    FG_EDITOR = "#dcdfe4"          # Genel kod metni
    FG_GUTTER = "#4b5975"          # Satır numaraları yazısı
    FG_CONSOLE = "#a5b4fc"         # Terminal normal yazı
    FG_CONSOLE_ERROR = "#ff5f5f"   # Terminal hata
    FG_CONSOLE_SUCCESS = "#43e68e" # Terminal başarılı
    FG_MUTED = "#6c7a9c"           # İkincil soluk yazılar
    FG_TITLE = "#ffffff"

    ACCENT = "#2954ff"             # Canlı Mavi (Run butonu, aktif sekme vs)
    ACCENT_HOVER = "#4070ff"
    ACCENT_ACTIVE = "#1a46cc"
    GREEN = "#10b981"              # Çevrimiçi / Başarı yeşili

    BUTTON_SECONDARY_BG = "#151d30" # İkincil butonlar (Geri Al vb)
    BUTTON_SECONDARY_HOVER = "#1c2640"
    BORDER = "#1f2a47"              # Panel ayırıcı çizgiler

    # Daha canlı Syntax Highlighting (Görsele uygun)
    SYNTAX_KEYWORD = "#c678dd"      # Mor (import, def, from vb.)
    SYNTAX_STRING = "#98c379"       # Yeşil (Metinler)
    SYNTAX_COMMENT = "#5c6370"      # Gri (Yorumlar)
    SYNTAX_NUMBER = "#d19a66"       # Turuncu (Sayılar)
    SYNTAX_FUNCTION = "#61afef"     # Mavi (Fonksiyon İsimleri)

    FONT_FAMILY_UI = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"

    FONT_UI = (FONT_FAMILY_UI, 10)
    FONT_UI_BOLD = (FONT_FAMILY_UI, 10, "bold")
    FONT_UI_SMALL = (FONT_FAMILY_UI, 9)
    FONT_TITLE = (FONT_FAMILY_UI, 12, "bold")
    FONT_EDITOR = (FONT_FAMILY_MONO, 12)
    FONT_CONSOLE = (FONT_FAMILY_MONO, 10)

    PAD_SM = 4
    PAD_MD = 8
    PAD_LG = 16


def load_icon(filename, size=None):
    path = os.path.join(config.ASSETS_DIR, filename)
    try:
        img = tk.PhotoImage(file=path)
        if size and img.width() != size:
            factor = max(1, round(img.width() / size))
            img = img.subsample(factor, factor)
        return img
    except Exception:
        return None

# =============================================================================
# ai_assistant.py
# =============================================================================

SYSTEM_PROMPT = "You are an expert Python coding assistant embedded inside a code editor."

CHAT_SYSTEM_PROMPT = """Sen, kullanıcının Python kod editörüne entegre edilmiş süper yetenekli bir yapay zeka asistanısın.
Kullanıcının çalışma alanı 'dosyam/' klasörüdür.

KULLANICI VAR OLAN DOSYAYI GÜNCELLEMENİ İSTERSE VEYA YENİ DOSYA İSTERSE KESİNLİKLE ŞU ETİKETİ KULLAN:
<create_file filename="dosya_adi.py">
# kodlar buraya gelecek
</create_file>

KLASÖR İSTERSE:
<create_folder foldername="klasor_adi" />

ÖNEMLİ KURAL: Kullanıcı var olan bir dosyadaki hatayı düzeltmeni veya ekleme yapmanı isterse, harici veya farklı isimde yeni bir dosya üretme! Doğrudan orijinal dosyanın adıyla (örn: <create_file filename="orijinal_dosya.py">) etiket oluştur ve tüm kodun son, düzeltilmiş halini içine yaz.

Etiketler dışındaki tüm yazıların kullanıcıya mesaj olarak gösterilecektir. Ne yaptığını kısaca anlat."""


class AIAssistantError(Exception):
    pass


@dataclass
class AISuggestion:
    original_code: str
    instruction: str
    suggested_code: str


class AIAssistant:
    def __init__(self):
        self._client = None

    def reset_client(self):
        self._client = None

    def _get_client(self):
        if OpenAI is None:
            raise AIAssistantError("openai modülü kurulu değil.")
        if not config.OPENAI_API_KEY:
            raise AIAssistantError("OpenAI API Key henüz girilmedi.")
        if self._client is None:
            self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        return self._client

    def get_suggestion(self, selected_code: str, instruction: str = "") -> AISuggestion:
        instruction = (instruction or "").strip()
        client = self._get_client()
        user_message = f"Instruction: {instruction}\n\n---\nCode:\n{selected_code}"
        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
                max_tokens=config.AI_MAX_TOKENS, temperature=config.AI_TEMPERATURE,
            )
        except Exception as exc:
            raise AIAssistantError(f"Hata: {exc}") from exc
        suggestion = response.choices[0].message.content.strip()
        if suggestion.startswith("```"):
            suggestion = "\n".join(suggestion.split("\n")[1:-1])
        return AISuggestion(original_code=selected_code, instruction=instruction, suggested_code=suggestion)

    def chat(self, messages: list) -> str:
        client = self._get_client()
        api_messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL, messages=api_messages,
                max_tokens=config.AI_MAX_TOKENS, temperature=config.AI_TEMPERATURE,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            raise AIAssistantError(f"Hata: {exc}") from exc


# =============================================================================
# editor_tab.py
# =============================================================================

# Sözdizimi renklendirmesi daha detaylandırıldı
_PATTERNS = [
    ("comment", r"(#.*)", theme.SYNTAX_COMMENT),
    ("string", r"(\".*?\"|'.*?'|\"\"\".*?\"\"\"|'''.*?''')", theme.SYNTAX_STRING),
    ("function", r"\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", theme.SYNTAX_FUNCTION), # Fonksiyon isimleri mavi
    ("keyword", r"\b(" + "|".join(keyword.kwlist) + r")\b", theme.SYNTAX_KEYWORD),
    ("number", r"\b(\d+\.?\d*)\b", theme.SYNTAX_NUMBER),
]


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, width=48, bg=theme.BG_EDITOR_GUTTER, highlightthickness=0, **kwargs)
        self.text_widget = text_widget

    def redraw(self, *_args):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline_info = self.text_widget.dlineinfo(i)
            if dline_info is None:
                break
            line_num = str(i).split(".")[0]
            self.create_text(38, dline_info[1], anchor="ne", text=line_num, fill=theme.FG_GUTTER, font=(theme.FONT_FAMILY_MONO, 11))
            i = self.text_widget.index(f"{i}+1line")


class SyntaxHighlighter:
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        for name, pattern, color in _PATTERNS:
            self.text_widget.tag_configure(name, foreground=color)
        self.text_widget.tag_raise("string")
        self.text_widget.tag_raise("comment")
        self._after_id = None

    def schedule_highlight(self, delay_ms: int = 120):
        if self._after_id:
            self.text_widget.after_cancel(self._after_id)
        self._after_id = self.text_widget.after(delay_ms, self.highlight)

    def highlight(self):
        content = self.text_widget.get("1.0", tk.END)
        for name, pattern, _ in _PATTERNS:
            self.text_widget.tag_remove(name, "1.0", tk.END)
            for match in re.finditer(pattern, content, re.MULTILINE):
                # Sadece def ismini vurgulamak için özel grup yakalama
                if name == "function" and match.lastindex == 1:
                    self.text_widget.tag_add(name, f"1.0+{match.start(1)}c", f"1.0+{match.end(1)}c")
                else:
                    self.text_widget.tag_add(name, f"1.0+{match.start()}c", f"1.0+{match.end()}c")


class EditorTab(tk.Frame):
    _untitled_counter = 0

    def __init__(self, master, app, initial_text: str = "", file_path: Optional[str] = None):
        super().__init__(master, bg=theme.BG_EDITOR)
        self.app, self.file_path, self.is_modified = app, file_path, False
        if not file_path:
            EditorTab._untitled_counter += 1
            self._untitled_id = EditorTab._untitled_counter
        else:
            self._untitled_id = None

        self.text = tk.Text(self, bg=theme.BG_EDITOR, fg=theme.FG_EDITOR, insertbackground="#ffffff",
                             font=theme.FONT_EDITOR, undo=True, maxundo=100, autoseparators=True, wrap="none",
                             borderwidth=0, highlightthickness=0, padx=10, pady=8)
        self.line_numbers = LineNumbers(self, self.text)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._on_scroll)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.line_numbers.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.highlighter = SyntaxHighlighter(self.text)

        self.text.bind("<KeyRelease>", self._on_change)
        self.text.bind("<<Modified>>", self._on_modified_flag)
        self.text.bind("<Return>", self._on_return_key)
        self.text.bind("<KP_Enter>", self._on_return_key)

        if initial_text:
            self.text.insert("1.0", initial_text)
        self.text.edit_modified(False)
        self.highlighter.highlight()
        self.line_numbers.redraw()

    def _on_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.redraw()

    def _on_change(self, event=None):
        if event and event.char in (" ", "\n", "\t"):
            self.text.edit_separator()
        self.line_numbers.redraw()
        self.highlighter.schedule_highlight()
        self.app._update_cursor_status()

    def _on_modified_flag(self, _event=None):
        if self.text.edit_modified():
            self.is_modified = True
            self.app._refresh_tab_title(self)
            self.text.edit_modified(False)

    def _on_return_key(self, _event):
        try:
            line_text = self.text.get("insert linestart", "insert")
            indent_match = re.match(r"^([ \t]*)", line_text)
            indent = indent_match.group(1) if indent_match else ""
            if line_text.rstrip().endswith(":"):
                indent += "    "
            self.text.insert(tk.INSERT, "\n" + indent)
            self.text.see(tk.INSERT)
            return "break"
        except Exception:
            return None

    @property
    def display_name(self) -> str:
        return os.path.basename(self.file_path) if self.file_path else f"Untitled-{self._untitled_id}"

    @property
    def tab_label(self) -> str:
        return f"{'● ' if self.is_modified else ''}{self.display_name}  ✖"

    def get_code(self) -> str:
        return self.text.get("1.0", "end-1c")

    def mark_saved(self, file_path: str):
        self.file_path = file_path
        self.is_modified = False
        self.app._refresh_tab_title(self)


# =============================================================================
# editor_app.py
# =============================================================================

WELCOME_SNIPPET = '''"""
Sotstech AI Asistanlı Editöre Hoş Geldin!

- Sürükle ve Bırak: Açık sekmelerini sürükleyerek yerlerini değiştirebilirsin.
- Doğrudan Silme: Sekmedeki (✖) ikonunun tam üzerine basarak dosyayı direkt silebilirsin.
  (İsmin üstüne tıklarsan normal sekme değişimi yapar, silinmez!)
- Otonom Ajan: Sohbete "otonom" yazıp otomatik tamamlayarak sistemi döngüye sokabilirsin.
"""
print("Otonom asistan devrede!")
'''


class AICodeStudio:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.ai_assistant = AIAssistant()
        self.chat_history = []
        self._icons = {}

        # Otonom mod değişkenleri
        self._autonomous_mode = False
        self._auto_target_file = None
        self._pending_auto_run = False
        self._auto_step = 0

        self._load_icons()
        self._configure_root()
        self._configure_ttk_styles()
        self._build_title_bar()
        self._build_toolbar()
        self._build_main_layout()
        self._bind_shortcuts()

        loaded_any = False
        if os.path.exists(config.WORKSPACE_DIR):
            for fname in sorted(os.listdir(config.WORKSPACE_DIR)):
                if fname.endswith(".py") and not fname.startswith("."):
                    fpath = os.path.join(config.WORKSPACE_DIR, fname)
                    if os.path.isfile(fpath):
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                content = f.read()
                            self.new_tab(initial_text=content, file_path=fpath)
                            loaded_any = True
                        except Exception:
                            pass

        if not loaded_any:
            self.new_tab(initial_text=WELCOME_SNIPPET)

        self._append_chat_system("Merhaba! Dosyalarını oluşturmama veya düzenlememe yardımcı olabilirim.")
        self._update_title()

    def _load_icons(self):
        specs = {
            "logo": ("app_logo.png", 40),
            "python": ("python_icon.png", 16),
            "robot": ("robot_avatar.png", 30),
            "user": ("user_avatar.png", 30),
            "home": ("home_icon.png", 20),
            "code": ("code_icon.png", 20),
            "chat": ("chat_icon.png", 22),
            "settings": ("settings_icon.png", 22),
            "folder": ("folder_icon.png", 22),
            "chevron_down": ("chevron_down_icon.png", 18),
            "chat_white": ("chat_icon_white.png", 22),
            "folder_white": ("folder_icon_white.png", 22),
            "settings_white": ("settings_icon_white.png", 22),
        }
        for key, (fname, size) in specs.items():
            self._icons[key] = load_icon(fname, size)

    def icon(self, key):
        return self._icons.get(key)

    def _configure_root(self):
        self.root.overrideredirect(True)
        self.root.geometry(config.DEFAULT_WINDOW_SIZE)
        self.root.configure(bg=theme.BG_APP)
        self.root.title(config.APP_DISPLAY_TITLE)
        try:
            self.root.attributes("-alpha", 1.0)
        except Exception:
            pass
        self._maximized = False
        self._normal_geometry = config.DEFAULT_WINDOW_SIZE

    def _configure_ttk_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background=theme.BG_PANEL)
        style.configure("Toolbar.TFrame", background=theme.BG_APP)
        
        # Modern oval / kutu hissi için paddingler güncellendi
        style.configure("Accent.TButton", background=theme.ACCENT, foreground="#ffffff",
                         font=theme.FONT_UI_BOLD, padding=(16, 8), borderwidth=0, relief="flat")
        style.map("Accent.TButton", background=[("active", theme.ACCENT_HOVER)])
        
        style.configure("Secondary.TButton", background=theme.BUTTON_SECONDARY_BG, foreground=theme.FG_EDITOR,
                         font=theme.FONT_UI, padding=(14, 8), borderwidth=0, relief="flat")
        style.map("Secondary.TButton", background=[("active", theme.BUTTON_SECONDARY_HOVER)])
        
        style.configure("Titlebar.TButton", background=theme.BG_TITLEBAR, foreground=theme.FG_MUTED,
                         font=theme.FONT_UI, padding=(10, 4), borderwidth=0, relief="flat")
        style.map("Titlebar.TButton", background=[("active", theme.BUTTON_SECONDARY_BG)])
        
        style.configure("PanelTitle.TLabel", background=theme.BG_PANEL, foreground=theme.FG_EDITOR, font=theme.FONT_UI_BOLD)
        style.configure("TNotebook", background=theme.BG_APP, borderwidth=0, tabmargins=(10, 6, 0, 0))
        
        style.configure("TNotebook.Tab", background=theme.BG_TAB_IDLE, foreground=theme.FG_MUTED,
                         padding=(10, 7, 6, 7), font=theme.FONT_UI, borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", theme.BG_TAB_ACTIVE)], foreground=[("selected", "#ffffff")])

    def _build_title_bar(self):
        bar = tk.Frame(self.root, bg=theme.BG_TITLEBAR, height=44)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        bar.configure(height=56)
        left = tk.Frame(bar, bg=theme.BG_TITLEBAR)
        left.pack(side="left", padx=(16, 0))
        if self.icon("logo"):
            tk.Label(left, image=self.icon("logo"), bg=theme.BG_TITLEBAR).pack(side="left", padx=(0, 10))
        title_col = tk.Frame(left, bg=theme.BG_TITLEBAR)
        title_col.pack(side="left")
        tk.Label(title_col, text=config.APP_DISPLAY_TITLE, bg=theme.BG_TITLEBAR, fg=theme.FG_TITLE,
                 font=theme.FONT_TITLE).pack(side="top", anchor="w")
        tk.Label(title_col, text="Akıllı Kodlama Asistanınız", bg=theme.BG_TITLEBAR, fg=theme.FG_MUTED,
                 font=theme.FONT_UI_SMALL).pack(side="top", anchor="w")

        controls = tk.Frame(bar, bg=theme.BG_TITLEBAR)
        controls.pack(side="right")
        for symbol, cmd, hover_fg in (
            ("—", self._minimize, "#ffffff"),
            ("▢", self._toggle_maximize, "#ffffff"),
            ("✕", self._on_close, "#ff6961"),
        ):
            lbl = tk.Label(controls, text=symbol, bg=theme.BG_TITLEBAR, fg=theme.FG_MUTED,
                            font=theme.FONT_UI, width=4, height=2, cursor="hand2")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, c=cmd: c())
            lbl.bind("<Enter>", lambda e, w=lbl, fg=hover_fg: w.configure(fg=fg))
            lbl.bind("<Leave>", lambda e, w=lbl: w.configure(fg=theme.FG_MUTED))

        for widget in (bar, left, title_col):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)
            widget.bind("<Double-Button-1>", lambda e: self._toggle_maximize())

    def _start_drag(self, event):
        self._drag_x, self._drag_y = event.x, event.y

    def _do_drag(self, event):
        if self._maximized:
            return
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<Map>", self._on_restore_from_iconify)

    def _on_restore_from_iconify(self, _event=None):
        if self.root.state() == "normal":
            self.root.overrideredirect(True)
            self.root.unbind("<Map>")

    def _toggle_maximize(self):
        if self._maximized:
            self.root.geometry(self._normal_geometry)
            self._maximized = False
        else:
            self._normal_geometry = self.root.geometry()
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
            self._maximized = True

    def _safe_edit_action(self, virtual_event):
        try:
            self.active_tab().text.event_generate(virtual_event)
            self.active_tab().highlighter.schedule_highlight(0)
            self.active_tab().line_numbers.redraw()
        except Exception:
            pass

    def _build_toolbar(self):
        # Görseldeki Toolbar dizilimi
        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding=(theme.PAD_LG, 10))
        toolbar.pack(side="top", fill="x")

        ttk.Button(toolbar, text="↶  Geri Al", style="Secondary.TButton",
                   command=lambda: self._safe_edit_action("<<Undo>>")).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="↷  İleri Al", style="Secondary.TButton",
                   command=lambda: self._safe_edit_action("<<Redo>>")).pack(side="left", padx=(0, 8))
        
        self.run_btn = ttk.Button(toolbar, text="▶  Run", style="Accent.TButton", command=self.run_code)
        self.run_btn.pack(side="left", padx=(10, 0))

        ttk.Button(toolbar, text="✓  Son Kontrolleri Yap", style="Accent.TButton",
                   command=self.ai_full_check).pack(side="right")
        ttk.Button(toolbar, text="+  Yeni Tab", style="Secondary.TButton",
                   command=lambda: self.new_tab()).pack(side="right", padx=(0, 10))

    def _build_main_layout(self):
        body = tk.Frame(self.root, bg=theme.BG_APP)
        body.pack(side="top", fill="both", expand=True)

        self._build_icon_rail(body)

        self.main_paned = tk.PanedWindow(body, orient="horizontal", sashwidth=6, bg=theme.BORDER, bd=0, sashrelief="flat")
        self.main_paned.pack(side="left", fill="both", expand=True)

        self._build_ai_sidebar()
        self._build_editor_and_console()
        
        self.main_paned.add(self.main_paned.panes()[0], stretch="never", minsize=250)
        self.root.update_idletasks()
        self.main_paned.sash_place(0, 270, 0) # Sidebar biraz daha geniş

    def _build_icon_rail(self, parent):
        rail = tk.Frame(parent, bg=theme.BG_RAIL, width=84)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)

        self._rail_buttons = {}
        self._rail_active = "chat"
        entries = [("chat", "Sohbet", "chat", "chat_white"),
                   ("folder", "Dosyalar", "folder", "folder_white"),
                   ("settings", "Ayarlar", "settings", "settings_white")]

        top_wrap = tk.Frame(rail, bg=theme.BG_RAIL)
        top_wrap.pack(side="top", fill="x", pady=(20, 0))

        for key, label_text, icon_key, icon_key_active in entries:
            item = tk.Frame(top_wrap, bg=theme.BG_RAIL, cursor="hand2")
            item.pack(side="top", fill="x", pady=(0, 14))

            badge = tk.Frame(item, bg=theme.BG_RAIL, width=44, height=36)
            badge.pack(anchor="center")
            badge.pack_propagate(False)
            icon_lbl = tk.Label(badge, image=self.icon(icon_key), bg=theme.BG_RAIL)
            icon_lbl.pack(expand=True)

            text_lbl = tk.Label(item, text=label_text, bg=theme.BG_RAIL, fg=theme.FG_MUTED, font=theme.FONT_UI_SMALL)
            text_lbl.pack(anchor="center", pady=(4, 0))

            widgets = {"item": item, "badge": badge, "icon": icon_lbl, "text": text_lbl,
                       "icon_key": icon_key, "icon_key_active": icon_key_active}
            self._rail_buttons[key] = widgets

            for w in (item, badge, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, k=key: self._on_rail_click(k))

        bottom_wrap = tk.Frame(rail, bg=theme.BG_RAIL, height=44)
        bottom_wrap.pack(side="bottom", fill="x", pady=(0, 14))
        bottom_wrap.pack_propagate(False)
        chevron = tk.Label(bottom_wrap, image=self.icon("chevron_down"), bg=theme.BG_RAIL, cursor="hand2")
        chevron.pack(expand=True)
        chevron.bind("<Button-1>", lambda e: self._toggle_maximize())

        self._apply_rail_state()

    def _apply_rail_state(self):
        for k, w in self._rail_buttons.items():
            active = (k == self._rail_active)
            badge_bg = theme.ACCENT if active else theme.BG_RAIL
            w["badge"].configure(bg=badge_bg)
            w["icon"].configure(image=self.icon(w["icon_key_active"] if active else w["icon_key"]), bg=badge_bg)
            w["text"].configure(fg="#ffffff" if active else theme.FG_MUTED)
            w["item"].configure(bg=theme.BG_RAIL)
            w["text"].master.configure(bg=theme.BG_RAIL)

    def _on_rail_click(self, key):
        self._rail_active = key
        self._apply_rail_state()
        if key == "settings":
            self.manage_api_key()
        elif key == "folder":
            self.open_file()
    # -------------------------

    def _build_ai_sidebar(self):
        ai_sidebar = tk.Frame(self.main_paned, bg=theme.BG_PANEL)

        ai_top = tk.Frame(ai_sidebar, bg=theme.BG_PANEL)
        ai_top.pack(side="top", fill="x", padx=12, pady=12)
        if self.icon("robot"):
            tk.Label(ai_top, image=self.icon("robot"), bg=theme.BG_PANEL).pack(side="left", padx=(0, 8))
        tk.Label(ai_top, text="AI Asistan", bg=theme.BG_PANEL, fg="#ffffff", font=theme.FONT_UI_BOLD).pack(side="left")
        status = tk.Frame(ai_top, bg=theme.BG_PANEL)
        status.pack(side="right")
        tk.Label(status, text="●", bg=theme.BG_PANEL, fg=theme.GREEN, font=theme.FONT_UI_SMALL).pack(side="left")
        tk.Label(status, text=" Çevrimiçi", bg=theme.BG_PANEL, fg=theme.FG_MUTED, font=theme.FONT_UI_SMALL).pack(side="left")

        chat_scroll_frame = tk.Frame(ai_sidebar, bg=theme.BG_PANEL)
        chat_scroll_frame.pack(side="top", fill="both", expand=True, padx=6, pady=4)
        self.chat_canvas = tk.Canvas(chat_scroll_frame, bg=theme.BG_PANEL, highlightthickness=0, borderwidth=0)
        chat_vscroll = ttk.Scrollbar(chat_scroll_frame, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=chat_vscroll.set)
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        chat_vscroll.pack(side="right", fill="y")

        self.chat_messages_frame = tk.Frame(self.chat_canvas, bg=theme.BG_PANEL)
        self._chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_messages_frame, anchor="nw")
        self.chat_messages_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(self._chat_window, width=e.width))
        self._bind_chat_mousewheel()
        self._finish_ai_sidebar(ai_sidebar)

    def _bind_chat_mousewheel(self):
        def _on_wheel(event):
            if hasattr(event, "delta") and event.delta:
                step = -1 if event.delta > 0 else 1
            elif getattr(event, "num", None) == 4:
                step = -1
            elif getattr(event, "num", None) == 5:
                step = 1
            else:
                step = 0
            self.chat_canvas.yview_scroll(step, "units")
            return "break"

        def _bind_scope(_e=None):
            self.chat_canvas.bind_all("<MouseWheel>", _on_wheel)
            self.chat_canvas.bind_all("<Button-4>", _on_wheel)
            self.chat_canvas.bind_all("<Button-5>", _on_wheel)

        def _unbind_scope(_e=None):
            self.chat_canvas.unbind_all("<MouseWheel>")
            self.chat_canvas.unbind_all("<Button-4>")
            self.chat_canvas.unbind_all("<Button-5>")

        self.chat_canvas.bind("<Enter>", _bind_scope)
        self.chat_canvas.bind("<Leave>", _unbind_scope)
        self.chat_messages_frame.bind("<Enter>", _bind_scope)
        self.chat_messages_frame.bind("<Leave>", _unbind_scope)

    def _finish_ai_sidebar(self, ai_sidebar):
        chat_input_frame = tk.Frame(ai_sidebar, bg=theme.BG_PANEL)
        chat_input_frame.pack(side="bottom", fill="x", padx=10, pady=12)
        input_box = tk.Frame(chat_input_frame, bg=theme.BG_INPUT, highlightthickness=1, highlightbackground=theme.BORDER)
        input_box.pack(side="top", fill="x")

        tk.Label(input_box, text="📎", bg=theme.BG_INPUT, fg=theme.FG_MUTED, font=theme.FONT_UI).pack(side="left", padx=(10, 4), pady=8)
        self.chat_input = tk.Text(input_box, height=2, bg=theme.BG_INPUT, fg=theme.FG_EDITOR, font=theme.FONT_UI,
                                   borderwidth=0, highlightthickness=0, insertbackground="#ffffff")
        self.chat_input.pack(side="left", fill="both", expand=True, pady=8)
        self._set_placeholder()
        self.chat_input.bind("<FocusIn>", self._clear_placeholder)
        self.chat_input.bind("<FocusOut>", self._restore_placeholder)
        self.chat_input.bind("<KeyRelease>", self._on_chat_key_release)
        self.chat_input.bind("<Tab>", self._on_chat_tab)
        self.chat_input.bind("<Return>", self._on_chat_return)
        
        self.chat_input.tag_configure("ghost", foreground=theme.GREEN, font=theme.FONT_UI_BOLD)
        self.chat_input.tag_configure("agent", foreground="#ff4c4c", font=theme.FONT_UI_BOLD)

        send_wrap = tk.Frame(input_box, bg=theme.BG_INPUT)
        send_wrap.pack(side="right", padx=8, pady=8)
        send_btn = tk.Label(send_wrap, text="➤", bg=theme.ACCENT, fg="#ffffff", font=theme.FONT_UI_BOLD,
                             width=3, height=1, cursor="hand2")
        send_btn.pack()
        send_btn.bind("<Button-1>", lambda e: self.send_chat_message())

        self.main_paned.add(ai_sidebar, stretch="never", minsize=250)

    def _set_placeholder(self):
        self.chat_input.delete("1.0", tk.END)
        self.chat_input.insert("1.0", "Mesajınızı yazın...")
        self.chat_input.configure(fg=theme.FG_MUTED)
        self._placeholder_active = True

    def _clear_placeholder(self, _event=None):
        if getattr(self, "_placeholder_active", False):
            self.chat_input.delete("1.0", tk.END)
            self.chat_input.configure(fg=theme.FG_EDITOR)
            self._placeholder_active = False

    def _restore_placeholder(self, _event=None):
        if not self.chat_input.get("1.0", "end-1c").strip():
            self._set_placeholder()

    def _append_chat_system(self, text: str):
        row = tk.Frame(self.chat_messages_frame, bg=theme.BG_PANEL)
        row.pack(side="top", fill="x", pady=(4, 8), padx=10)
        tk.Label(row, text=text, bg=theme.BG_PANEL, fg=theme.FG_MUTED, font=theme.FONT_UI_SMALL,
                 wraplength=280, justify="center").pack(fill="x")
        self._scroll_chat_to_end()

    def _append_chat_bubble(self, sender: str, text: str, timestamp: str, extra_lines=None):
        is_user = sender == "user"
        row = tk.Frame(self.chat_messages_frame, bg=theme.BG_PANEL)
        row.pack(side="top", fill="x", pady=6, padx=10)

        header = tk.Frame(row, bg=theme.BG_PANEL)
        header.pack(side="top", fill="x")
        avatar_key = "user" if is_user else "robot"
        if self.icon(avatar_key):
            tk.Label(header, image=self.icon(avatar_key), bg=theme.BG_PANEL).pack(side="left", padx=(0, 6))
        tk.Label(header, text=("Sen" if is_user else "Asistan"), bg=theme.BG_PANEL,
                 fg=("#7cc4ff" if is_user else theme.GREEN), font=theme.FONT_UI_BOLD).pack(side="left")

        bubble = tk.Frame(row, bg=(theme.BG_BUBBLE_USER if is_user else theme.BG_BUBBLE_AI))
        bubble.pack(side="top", fill="x", pady=(4, 0))
        tk.Label(bubble, text=text, bg=bubble["bg"], fg=theme.FG_EDITOR, font=theme.FONT_UI,
                 wraplength=280, justify="left", anchor="w").pack(fill="x", padx=10, pady=(8, 4))

        if extra_lines:
            files_box = tk.Frame(bubble, bg=bubble["bg"])
            files_box.pack(fill="x", padx=10, pady=(0, 8))
            for fname, desc in extra_lines:
                line = tk.Frame(files_box, bg=bubble["bg"])
                line.pack(fill="x", pady=2)
                if self.icon("python"):
                    tk.Label(line, image=self.icon("python"), bg=bubble["bg"]).pack(side="left", padx=(0, 6))
                tk.Label(line, text=fname, bg=bubble["bg"], fg="#ffffff", font=theme.FONT_UI_SMALL).pack(side="left")
                if desc:
                    tk.Label(line, text=f"  →  {desc}", bg=bubble["bg"], fg=theme.FG_MUTED,
                              font=theme.FONT_UI_SMALL, wraplength=200, justify="left").pack(side="left")
        else:
            tk.Label(bubble, text=timestamp, bg=bubble["bg"], fg=theme.FG_MUTED,
                     font=theme.FONT_UI_SMALL).pack(anchor="e", padx=10, pady=(0, 6))

        self._scroll_chat_to_end()
        return row

    def _scroll_chat_to_end(self):
        self.chat_messages_frame.update_idletasks()
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)

    def _timestamp(self):
        import datetime
        return datetime.datetime.now().strftime("%H:%M")

    def _build_editor_and_console(self):
        right_paned = tk.PanedWindow(self.main_paned, orient="vertical", sashwidth=6, bg=theme.BORDER, bd=0, sashrelief="flat")
        self.main_paned.add(right_paned, stretch="always")

        editor_container = tk.Frame(right_paned, bg=theme.BG_EDITOR)
        tab_top = tk.Frame(editor_container, bg=theme.BG_APP)
        tab_top.pack(side="top", fill="x")

        self.notebook = ttk.Notebook(tab_top)
        self.notebook.pack(side="left", fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook.bind("<ButtonPress-1>", self._on_notebook_press)
        self.notebook.bind("<ButtonRelease-1>", self._on_notebook_release)
        self.notebook.bind("<B1-Motion>", self._on_notebook_motion)

        self.editor_notebook_holder = editor_container
        right_paned.add(editor_container, stretch="always", minsize=220)

        console_container = tk.Frame(right_paned, bg=theme.BG_CONSOLE)
        console_header = tk.Frame(console_container, bg=theme.BG_PANEL, height=34)
        console_header.pack(side="top", fill="x")
        console_header.pack_propagate(False)
        tab_chip = tk.Frame(console_header, bg=theme.BG_CONSOLE)
        tab_chip.pack(side="left", padx=(10, 0), pady=4)
        tk.Label(tab_chip, text="≡  Terminal", bg=theme.BG_CONSOLE, fg="#ffffff", font=theme.FONT_UI_SMALL,
                 padx=10, pady=4).pack(side="left")
        tk.Label(tab_chip, text=" ✕", bg=theme.BG_CONSOLE, fg=theme.FG_MUTED, font=theme.FONT_UI_SMALL,
                 cursor="hand2").pack(side="left", padx=(0, 6))
        tk.Label(console_header, text="+", bg=theme.BG_PANEL, fg=theme.FG_MUTED, font=theme.FONT_UI,
                 cursor="hand2").pack(side="left", padx=6)
        tk.Label(console_header, text="⧉", bg=theme.BG_PANEL, fg=theme.FG_MUTED, font=theme.FONT_UI,
                 cursor="hand2").pack(side="right", padx=10)

        self.console = tk.Text(console_container, bg=theme.BG_CONSOLE, fg=theme.FG_CONSOLE, font=theme.FONT_CONSOLE,
                                state="disabled", wrap="word", borderwidth=0, highlightthickness=0, padx=10, pady=8)
        self.console.pack(side="left", fill="both", expand=True)

        self.console.tag_configure("stdout", foreground=theme.FG_CONSOLE)
        self.console.tag_configure("stderr", foreground=theme.FG_CONSOLE_ERROR)
        self.console.tag_configure("success", foreground=theme.FG_CONSOLE_SUCCESS)
        self.console.tag_configure("system", foreground=theme.ACCENT, font=theme.FONT_UI_BOLD)
        right_paned.add(console_container, minsize=120)
        self._append_console("> ", "stdout")

    def _on_notebook_press(self, event):
        self._notebook_dragged = False
        try:
            self._active_tab_drag_index = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            self._active_tab_drag_index = None

    def _on_notebook_motion(self, event):
        if getattr(self, "_active_tab_drag_index", None) is None:
            return
        self._notebook_dragged = True
        try:
            target_index = self.notebook.index(f"@{event.x},{event.y}")
            if target_index != self._active_tab_drag_index:
                self.notebook.insert(target_index, self.notebook.tabs()[self._active_tab_drag_index])
                self._active_tab_drag_index = target_index
        except tk.TclError:
            pass

    def _on_notebook_release(self, event):
        if getattr(self, "_active_tab_drag_index", None) is None:
            return
        if not getattr(self, "_notebook_dragged", False):
            try:
                index = self.notebook.index(f"@{event.x},{event.y}")
                bbox = self.notebook.bbox(index)
                tab_right_edge = bbox[0] + bbox[2]
                if tab_right_edge - 26 <= event.x <= tab_right_edge:
                    self.close_specific_tab(index, force_delete=True)
                else:
                    self.notebook.select(index)
            except tk.TclError:
                pass
        self._active_tab_drag_index = None

    def close_specific_tab(self, index, force_delete=False):
        tab = self.notebook.nametowidget(self.notebook.tabs()[index])
        if force_delete:
            if tab.file_path and os.path.exists(tab.file_path):
                try:
                    os.remove(tab.file_path)
                    self._append_console(f"[Sistem] Dosya tamamen silindi: {tab.display_name}\n", "system")
                except Exception:
                    pass
            self.notebook.forget(tab)
            if not self.notebook.tabs():
                self.new_tab(initial_text=WELCOME_SNIPPET)
        else:
            if tab.is_modified and not self._confirm_discard_changes(tab):
                return
            self.notebook.forget(tab)
            if not self.notebook.tabs():
                self.new_tab(initial_text=WELCOME_SNIPPET)

    def _clear_chat_ghost(self):
        ranges = self.chat_input.tag_ranges("ghost")
        if ranges:
            self.chat_input.delete(ranges[0], ranges[1])

    def _on_chat_key_release(self, event):
        if event.keysym in ("Return", "Tab", "BackSpace", "space"):
            return
        self._clear_chat_ghost()
        text = self.chat_input.get("1.0", "insert")
        match = re.search(r'([A-Za-z0-9_.-]+)$', text)
        if match:
            word = match.group(1)
            
            if "otonom".startswith(word.lower()) and len(word) >= 2:
                remainder = "otonom (ajan)"[len(word):]
                self.chat_input.insert("insert", remainder, "ghost")
                self.chat_input.mark_set("insert", f"insert-{len(remainder)}c")
                return

            if len(word) >= 1:
                try:
                    files = [f for f in os.listdir(config.WORKSPACE_DIR) if f.startswith(word) and not f.startswith(".")]
                except Exception:
                    files = []
                if files:
                    best = files[0]
                    remainder = best[len(word):]
                    if remainder:
                        self.chat_input.insert("insert", remainder, "ghost")
                        self.chat_input.mark_set("insert", f"insert-{len(remainder)}c")

    def _apply_ghost_completion(self):
        ranges = self.chat_input.tag_ranges("ghost")
        if ranges:
            ghost_text = self.chat_input.get(ranges[0], ranges[1])
            self.chat_input.tag_remove("ghost", ranges[0], ranges[1])
            
            if "otonom" in ghost_text.lower():
                line_start = self.chat_input.index(f"{ranges[0]} linestart")
                self.chat_input.delete(line_start, ranges[1])
                self.chat_input.insert(line_start, "otonom (ajan) ", "agent")
            else:
                self.chat_input.mark_set("insert", ranges[1])
            return True
        return False

    def _on_chat_tab(self, event):
        if self._apply_ghost_completion():
            return "break"
        return None

    def _on_chat_return(self, event):
        if self._apply_ghost_completion():
            return "break"
        self.send_chat_message()
        return "break"

    def send_chat_message(self):
        self._clear_placeholder()
        user_text = self.chat_input.get("1.0", "end-1c").strip()
        if not user_text or getattr(self, "_placeholder_active", False):
            return
        self.chat_input.delete("1.0", tk.END)
        self._clear_chat_ghost()
        self._restore_placeholder()

        if user_text.lower() == "otonom iptal":
            self._autonomous_mode = False
            self._pending_auto_run = False
            self._append_chat_bubble("user", user_text, self._timestamp())
            self._append_chat_bubble("ai", "Otonom ajan devre dışı bırakıldı.", self._timestamp())
            return

        if "otonom (ajan)" in user_text:
            self._autonomous_mode = True
            self._auto_step = 1
            
            parts = user_text.split("otonom (ajan)", 1)
            after_text = parts[1].strip() if len(parts) > 1 else ""
            
            match = re.match(r'^([a-zA-Z0-9_.-]+\.py)', after_text)
            if match:
                target = match.group(1)
                prompt_text = after_text[len(target):].strip()
            else:
                target = "main.py"
                prompt_text = after_text

            self._auto_target_file = target
            self._pending_auto_run = True
            
            user_text = f"Otonom ajan aktif. Hedef dosya: {target}. İstenen görev: '{prompt_text}'. İlgili kodu eksiksiz, çalışmaya hazır tam dosya olarak oluştur/güncelle."
            self._append_chat_bubble("ai", f"🚀 [Durum {self._auto_step}] Otonom hedef belirlendi ({target}). Görev başlatıldı, kodlar yazılıyor...", self._timestamp())
        mentioned_files = []
        try:
            workspace_files = [f for f in os.listdir(config.WORKSPACE_DIR) if not f.startswith(".")]
            for f in workspace_files:
                if f in user_text:
                    mentioned_files.append(f)
        except Exception:
            pass

        display_text = user_text
        actual_prompt = user_text

        if mentioned_files:
            file_contexts = []
            for f in mentioned_files:
                path = os.path.join(config.WORKSPACE_DIR, f)
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8") as file_obj:
                        file_contexts.append(f"--- {f} İçeriği ---\n```python\n{file_obj.read()}\n```")
            if file_contexts:
                context_str = "\n\n".join(file_contexts)
                if user_text.strip() in mentioned_files and len(user_text.split()) == 1:
                    display_text = f"📄 '{user_text}' dosyasını analiz et/güncelle."
                actual_prompt = (
                    f"{user_text}\n\n[SİSTEM NOTU: Kullanıcı projendeki bazı dosyalardan bahsetti. Mevcut kodlar:\n{context_str}\n\n"
                    f"ÖNEMLİ KURAL: Lütfen değişiklikleri yapmak için yeni veya farklı isimde bir dosya üretme! Doğrudan orijinal var olan dosyanın adını kullanarak (<create_file filename=\"dosya_adi.py\"> etiketiyle) kodun son/güncel halini yaz.]"
                )

        self._append_chat_bubble("user", display_text, self._timestamp())
        self.chat_history.append({"role": "user", "content": actual_prompt})
        self._set_status("Yapay Zeka düşünüyor...")

        def _worker():
            try:
                response_text = self.ai_assistant.chat(self.chat_history)
                self.chat_history.append({"role": "assistant", "content": response_text})
                self.root.after(0, self._process_ai_response, response_text, self._pending_auto_run)
            except Exception as e:
                self.root.after(0, self._append_chat_bubble, "ai", f"Hata: {e}", self._timestamp())
            finally:
                self.root.after(0, self._set_status, "Hazır.")

        threading.Thread(target=_worker, daemon=True).start()

    def _process_ai_response(self, text: str, auto_trigger_run: bool = False):
        clean_text = re.sub(r'<create_folder.*?>', '', text)
        clean_text = re.sub(r'<create_file.*?>.*?</create_file>', '', clean_text, flags=re.DOTALL).strip()

        folders = re.findall(r'<create_folder\s+foldername=[\'"]([^\'"]+)[\'"]\s*/?>', text)
        for folder in folders:
            os.makedirs(os.path.join(config.WORKSPACE_DIR, folder), exist_ok=True)

        files = re.findall(r'<create_file\s+filename=[\'"]([^\'"]+)[\'"]>(.*?)</create_file>', text, flags=re.DOTALL)
        file_summary = []
        for fname, content in files:
            content = content.strip()
            if content.startswith("```python"):
                content = content[9:].strip()
            elif content.startswith("```"):
                content = content[3:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()

            path = os.path.join(config.WORKSPACE_DIR, fname)
            os.makedirs(os.path.dirname(path) or config.WORKSPACE_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            existing_tab = None
            for tab_id in self.notebook.tabs():
                t = self.notebook.nametowidget(tab_id)
                if t.file_path == path:
                    existing_tab = t
                    break

            if existing_tab:
                existing_tab.text.delete("1.0", tk.END)
                existing_tab.text.insert("1.0", content)
                existing_tab.highlighter.highlight()
                existing_tab.line_numbers.redraw()
                existing_tab.is_modified = False
                self._refresh_tab_title(existing_tab)
                self.notebook.select(existing_tab)
                file_summary.append((fname, "güncellendi"))
            else:
                self.new_tab(initial_text=content, file_path=path)
                file_summary.append((fname, "oluşturuldu"))

        body_text = clean_text if clean_text else "İşlemler tamamlandı, dosyalar hazır!"
        self._append_chat_bubble("ai", body_text, self._timestamp(), extra_lines=file_summary or None)
        
        if auto_trigger_run and getattr(self, "_autonomous_mode", False):
            self._auto_step += 1
            self._append_chat_bubble("ai", f"⚙️ [Durum {self._auto_step}] Kodu yazdım ve kaydettim. Dosya terminalde çalıştırılıyor ve sonuç bekleniyor...", self._timestamp())
            self._append_console(f"\n[Otonom] AI güncellemeyi bitirdi, {self._auto_target_file} çalıştırılıyor...\n", "system")
            self.root.after(1000, lambda: self.run_code(run_target=self._auto_target_file))

    def _on_tab_changed(self, _event=None):
        self._update_cursor_status()
        self._update_title()

    def new_tab(self, initial_text: str = "", file_path=None) -> EditorTab:
        tab = EditorTab(self.notebook, self, initial_text=initial_text, file_path=file_path)
        self.notebook.add(tab, text=tab.tab_label, image=self.icon("python"), compound="left")
        self.notebook.select(tab)
        return tab

    def active_tab(self) -> EditorTab:
        return self.notebook.nametowidget(self.notebook.select())

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

    def _update_cursor_status(self):
        try:
            tab = self.active_tab()
        except Exception:
            return
        line, col = tab.text.index(tk.INSERT).split(".")

    def _set_status(self, message: str):
        pass  

    def _bind_shortcuts(self):
        self.root.bind("<F5>", lambda e: self.run_code())
        self.root.bind("<Control-t>", lambda e: self.new_tab())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def open_file(self):
        path = filedialog.askopenfilename(initialdir=config.WORKSPACE_DIR, filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.new_tab(initial_text=content, file_path=path)

    def save_file(self):
        tab = self.active_tab()
        if tab.file_path is None:
            path = filedialog.asksaveasfilename(initialdir=config.WORKSPACE_DIR, defaultextension=".py")
            if not path:
                return
            tab.file_path = path
        with open(tab.file_path, "w", encoding="utf-8") as f:
            f.write(tab.get_code())
        tab.mark_saved(tab.file_path)

    def _confirm_discard_changes(self, tab: EditorTab) -> bool:
        if not tab.is_modified:
            return True
        answer = messagebox.askyesnocancel("Kaydedilmedi", f"'{tab.display_name}' kaydedilsin mi?")
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
            name = self.active_tab().display_name
        except Exception:
            name = "Untitled"
        self.root.title(f"{name} — {config.APP_DISPLAY_TITLE}")

    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.configure(state="disabled")

    def _append_console(self, text: str, tag: str):
        self.console.configure(state="normal")
        self.console.insert(tk.END, text, tag)
        self.console.see(tk.END)
        self.console.configure(state="disabled")

    def _parse_python_error(self, stderr_text: str) -> str:
        lines = stderr_text.strip().split('\n')
        relevant = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('File "') and ".py" in line_stripped:
                relevant.append(line_stripped)
            elif "Error:" in line_stripped or "Exception:" in line_stripped or (relevant and not line_stripped.startswith(" ")):
                relevant.append(line_stripped)
        
        if len(relevant) > 4:
            return "\n".join(relevant[-4:])
        return "\n".join(relevant) if relevant else stderr_text[-400:]

    def _trigger_autonomous_fix(self, parsed_error: str):
        file_contexts = []
        for f in os.listdir(config.WORKSPACE_DIR):
            if f.endswith(".py") and not f.startswith("."):
                path = os.path.join(config.WORKSPACE_DIR, f)
                with open(path, "r", encoding="utf-8") as file_obj:
                    file_contexts.append(f"--- {f} ---\n```python\n{file_obj.read()}\n```")
        
        context_str = "\n\n".join(file_contexts)
        prompt = (
            f"Kodu çalıştırdığımda şu hatayı aldım:\n\n{parsed_error}\n\n"
            f"Projedeki mevcut dosyalarım:\n{context_str}\n\n"
            f"Lütfen hatanın kaynağını analiz et ve sadece hata olan dosyaları/dosyayı `<create_file>` etiketiyle düzeltip gönder. "
            f"Bana kodu tamamen düzeltilmiş, çalışmaya hazır formda ilet."
        )

        self.chat_history.append({"role": "user", "content": prompt})

        def ai_worker():
            try:
                response_text = self.ai_assistant.chat(self.chat_history)
                self.chat_history.append({"role": "assistant", "content": response_text})
                self.root.after(0, self._process_ai_response, response_text, True) 
            except Exception as e:
                self.root.after(0, self._append_chat_bubble, "ai", f"Otonom Hata: {e}", self._timestamp())
                self._autonomous_mode = False

        threading.Thread(target=ai_worker, daemon=True).start()

    def run_code(self, run_target=None):
        self.clear_console()
        self._set_status("Çalıştırılıyor...")

        if run_target:
            target = os.path.join(config.WORKSPACE_DIR, run_target)
            if not os.path.exists(target):
                self._append_console(f"[Hata] Otonom hedef dosya '{run_target}' bulunamadı!\n", "stderr")
                return
        else:
            tab = self.active_tab()
            code = tab.get_code()
            if not code.strip():
                return
            target = os.path.join(config.WORKSPACE_DIR, ".__sotstech_run.py")
            with open(target, "w", encoding="utf-8") as f:
                f.write(code)

        def _worker(attempt=1):
            proc = None
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-u", target],
                    cwd=config.WORKSPACE_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace"
                )
                stderr_lines = []

                def read_stdout(stream):
                    for line in iter(stream.readline, ''):
                        if line:
                            self.root.after(0, self._append_console, line, "stdout")
                    stream.close()

                def read_stderr(stream):
                    for line in iter(stream.readline, ''):
                        if line:
                            stderr_lines.append(line)
                            self.root.after(0, self._append_console, line, "stderr")
                    stream.close()

                t_out = threading.Thread(target=read_stdout, args=(proc.stdout,), daemon=True)
                t_err = threading.Thread(target=read_stderr, args=(proc.stderr,), daemon=True)
                t_out.start()
                t_err.start()
                proc.wait()
                t_out.join(timeout=2)
                t_err.join(timeout=2)

                full_stderr = "".join(stderr_lines)

                if proc.returncode != 0:
                    if "numpy.dtype size changed" in full_stderr or "Expected 96 from C header" in full_stderr:
                        if attempt <= 2:
                            self.root.after(0, self._append_console, "\n[Sistem] NumPy sürüm uyuşmazlığı tespit edildi. Otomatik onarılıyor...\n", "system")
                            subprocess.run([sys.executable, "-m", "pip", "install", "numpy<2", "--force-reinstall"], capture_output=True)
                            self.root.after(0, self._append_console, "[Sistem] Onarım tamamlandı. Kod tekrar çalıştırılıyor...\n\n", "success")
                            _worker(attempt=attempt + 1)
                            return

                    module_match = re.search(r"ModuleNotFoundError:\s*No module named ['\"]([\w\.]+)['\"]", full_stderr)
                    if module_match and attempt <= 2:
                        mod_name = module_match.group(1).split(".")[0]
                        if mod_name == "sklearn":
                            mod_name = "scikit-learn"
                        if mod_name == "cv2":
                            mod_name = "opencv-python"
                        if mod_name == "PIL":
                            mod_name = "Pillow"
                        self.root.after(0, self._append_console, f"\n[Sistem] Eksik kütüphane ({mod_name}) tespit edildi. Kuruluyor...\n", "system")
                        subprocess.run([sys.executable, "-m", "pip", "install", mod_name], capture_output=True)
                        self.root.after(0, self._append_console, f"[Sistem] {mod_name} başarıyla kuruldu. Tekrar çalıştırılıyor...\n\n", "success")
                        _worker(attempt=attempt + 1)
                        return
                    
                    if getattr(self, "_autonomous_mode", False):
                        self._auto_step += 1
                        parsed_error = self._parse_python_error(full_stderr)
                        self.root.after(0, self._append_chat_bubble, "ai", f"⚠️ [Durum {self._auto_step}] Kodda hata tespit ettim! Hata analiz edilip yeni çözüm senaryosu üretiliyor...", self._timestamp())
                        self.root.after(0, self._trigger_autonomous_fix, parsed_error)
                        return

                if proc.returncode == 0:
                    self.root.after(0, self._append_console, "\n[İşlem başarıyla tamamlandı]\n> ", "success")
                    if getattr(self, "_autonomous_mode", False):
                        self._auto_step += 1
                        self.root.after(0, self._append_chat_bubble, "ai", f"✅ [Durum {self._auto_step}] Başarılı! Kod sıfır hata ile çalışıyor. Ana hedefe sorunsuz ulaşıldı ve ajan kapatıldı.", self._timestamp())
                        self._autonomous_mode = False 

            except Exception as e:
                self.root.after(0, self._append_console, f"\n[Hata] {e}\n", "stderr")
            finally:
                if attempt == 1 or (proc is not None and proc.returncode == 0):
                    self.root.after(0, self._set_status, "Hazır.")
                    if not run_target:
                        try:
                            os.remove(target)
                        except Exception:
                            pass

        threading.Thread(target=_worker, daemon=True).start()

    def ai_full_check(self):
        tab = self.active_tab()
        code = tab.get_code()
        if not code.strip():
            return
        self._set_status("Analiz ediliyor...")
        self.root.config(cursor="watch")

        instruction = "Tüm kodu kontrol et. Hataları/eksikleri bul ve düzelt. Sadece KOD kısmını (salt metin olarak, markdown olmadan) KOD: başlığından sonra ver. Öncesinde ise DÜZELTMELER: diyerek listele."

        def _worker():
            try:
                suggestion = self.ai_assistant.get_suggestion(code, instruction)
                self.root.after(0, self._show_ai_full_check_dialog, tab, suggestion.suggested_code)
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Analiz başarısız:\n{exc}"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))
                self.root.after(0, lambda: self._set_status("Hazır."))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_ai_full_check_dialog(self, tab, response_text):
        dialog = tk.Toplevel(self.root)
        dialog.title("Son Kontrol Sonuçları")
        dialog.geometry("900x650")
        dialog.configure(bg=theme.BG_PANEL)

        explanations = "Sorun bulunamadı."
        fixed_code = response_text
        if "KOD:" in response_text:
            parts = response_text.split("KOD:", 1)
            explanations = parts[0].replace("DÜZELTMELER:", "").strip()
            fixed_code = parts[1].strip()
            if fixed_code.startswith("```python"):
                fixed_code = fixed_code[9:]
            if fixed_code.startswith("```"):
                fixed_code = fixed_code[3:]
            if fixed_code.endswith("```"):
                fixed_code = fixed_code[:-3]
            fixed_code = fixed_code.strip()

        ttk.Label(dialog, text="Yapay Zeka Analiz Raporu:", style="PanelTitle.TLabel").pack(pady=4)
        tk.Label(dialog, text=explanations, bg=theme.BG_PANEL, fg=theme.FG_EDITOR, wraplength=850, justify="left").pack(pady=4)

        text_widget = tk.Text(dialog, bg=theme.BG_EDITOR, fg=theme.FG_EDITOR, font=theme.FONT_EDITOR)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", fixed_code)

        def apply_changes():
            tab.text.delete("1.0", tk.END)
            tab.text.insert("1.0", text_widget.get("1.0", "end-1c"))
            tab.highlighter.highlight()
            tab.line_numbers.redraw()
            tab.is_modified = True
            self._refresh_tab_title(tab)
            dialog.destroy()

        ttk.Button(dialog, text="Onaylıyorum (Kodu Güncelle)", style="Accent.TButton", command=apply_changes).pack(pady=10)

    def manage_api_key(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("API Key")
        dialog.geometry("480x150")
        dialog.configure(bg=theme.BG_PANEL)
        key_var = tk.StringVar()
        tk.Entry(dialog, textvariable=key_var, show="*", bg=theme.BG_INPUT, fg=theme.FG_EDITOR,
                  insertbackground="#ffffff", relief="flat").pack(fill="x", padx=20, pady=20, ipady=6)

        def save():
            config.save_api_key(key_var.get())
            config.OPENAI_API_KEY = key_var.get()
            self.ai_assistant.reset_client()
            dialog.destroy()

        ttk.Button(dialog, text="Kaydet", style="Accent.TButton", command=save).pack()


def main():
    root = tk.Tk()
    try:
        AICodeStudio(root)
    except Exception:
        return
    root.mainloop()


if __name__ == "__main__":
    main()
