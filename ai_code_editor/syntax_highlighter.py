"""
syntax_highlighter.py
----------------------
A dependency-free, "good enough" Python syntax highlighter for the Tk
Text widget. It re-tags the visible buffer on every keystroke (debounced)
using simple regular expressions. This is not a full tokenizer, but it
gives the editor a professional, IDE-like appearance without adding any
third-party dependencies.
"""

import re
import keyword
import tkinter as tk

import theme

_KEYWORDS = r"\b(" + "|".join(keyword.kwlist) + r")\b"
_BUILTINS = r"\b(" + "|".join([
    "print", "len", "range", "str", "int", "float", "list", "dict", "set",
    "tuple", "bool", "open", "input", "type", "isinstance", "enumerate",
    "zip", "map", "filter", "sum", "min", "max", "sorted", "reversed",
    "super", "self", "None", "True", "False",
]) + r")\b"
_STRING = r"(\".*?\"|'.*?'|\"\"\".*?\"\"\"|'''.*?''')"
_COMMENT = r"(#.*)"
_NUMBER = r"\b(\d+\.?\d*)\b"
_DEFCLASS = r"\b(def|class)\s+(\w+)"

_PATTERNS = [
    ("comment", _COMMENT, theme.SYNTAX_COMMENT),
    ("string", _STRING, theme.SYNTAX_STRING),
    ("keyword", _KEYWORDS, theme.SYNTAX_KEYWORD),
    ("builtin", _BUILTINS, theme.SYNTAX_BUILTIN),
    ("number", _NUMBER, theme.SYNTAX_NUMBER),
]


class SyntaxHighlighter:
    """Attaches lightweight syntax highlighting to a Tk Text widget."""

    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self._configure_tags()
        self._after_id = None

    def _configure_tags(self):
        for name, _, color in _PATTERNS:
            self.text_widget.tag_configure(name, foreground=color)
        self.text_widget.tag_configure(
            "defclass", foreground=theme.SYNTAX_DEFCLASS, font=(theme.FONT_FAMILY_MONO, 12, "bold")
        )
        # Ensure strings/comments paint over keywords found inside them.
        self.text_widget.tag_raise("string")
        self.text_widget.tag_raise("comment")

    def schedule_highlight(self, delay_ms: int = 120):
        """Debounce highlighting so it doesn't run on every single keystroke."""
        if self._after_id is not None:
            self.text_widget.after_cancel(self._after_id)
        self._after_id = self.text_widget.after(delay_ms, self.highlight)

    def highlight(self):
        content = self.text_widget.get("1.0", tk.END)

        for name, _, _ in _PATTERNS:
            self.text_widget.tag_remove(name, "1.0", tk.END)
        self.text_widget.tag_remove("defclass", "1.0", tk.END)

        for name, pattern, _ in _PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add(name, start, end)

        for match in re.finditer(_DEFCLASS, content):
            start = f"1.0+{match.start(2)}c"
            end = f"1.0+{match.end(2)}c"
            self.text_widget.tag_add("defclass", start, end)
