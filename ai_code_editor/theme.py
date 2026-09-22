"""
theme.py
--------
Centralised visual design tokens for the AI Code Studio editor.
Keeping colours, fonts and spacing in one place makes the whole
application feel consistent and makes future re-skinning trivial.
"""

# ---------------------------------------------------------------------------
# Palette (inspired by modern dark IDE themes)
# ---------------------------------------------------------------------------
BG_APP = "#1e1e1e"            # Main application background
BG_PANEL = "#252526"          # Side / toolbar panels
BG_EDITOR = "#1e1e1e"         # Code editor background
BG_EDITOR_GUTTER = "#1e1e1e"  # Line-number gutter background
BG_CONSOLE = "#181818"        # Output console background
BG_STATUSBAR = "#007acc"      # Bottom status bar (accent)
BG_TITLEBAR = "#323233"       # Menu bar background

FG_EDITOR = "#d4d4d4"         # Default editor text colour
FG_GUTTER = "#6e7681"         # Line-number colour
FG_CONSOLE = "#cccccc"        # Console text colour
FG_CONSOLE_ERROR = "#f14c4c"  # Console error text colour
FG_CONSOLE_SUCCESS = "#4ec9b0"
FG_MUTED = "#9d9d9d"
FG_STATUSBAR = "#ffffff"

ACCENT = "#007acc"            # Primary accent (buttons, highlights)
ACCENT_HOVER = "#1b8ad2"
ACCENT_ACTIVE = "#005fa3"

BUTTON_SECONDARY_BG = "#3a3d41"
BUTTON_SECONDARY_HOVER = "#45494e"

BORDER = "#2d2d2d"

# Syntax highlighting colours (lightweight, no external deps)
SYNTAX_KEYWORD = "#569cd6"
SYNTAX_STRING = "#ce9178"
SYNTAX_COMMENT = "#6a9955"
SYNTAX_NUMBER = "#b5cea8"
SYNTAX_BUILTIN = "#4ec9b0"
SYNTAX_DEFCLASS = "#dcdcaa"

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_FAMILY_UI = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

FONT_UI = (FONT_FAMILY_UI, 10)
FONT_UI_BOLD = (FONT_FAMILY_UI, 10, "bold")
FONT_UI_SMALL = (FONT_FAMILY_UI, 9)
FONT_TITLE = (FONT_FAMILY_UI, 12, "bold")
FONT_EDITOR = (FONT_FAMILY_MONO, 12)
FONT_CONSOLE = (FONT_FAMILY_MONO, 10)

# ---------------------------------------------------------------------------
# Spacing
# ---------------------------------------------------------------------------
PAD_SM = 4
PAD_MD = 8
PAD_LG = 16
