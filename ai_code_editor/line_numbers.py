"""
line_numbers.py
----------------
A Canvas-based line-number gutter that stays synchronised with a paired
Text widget, giving the editor a professional IDE look and feel.
"""

import tkinter as tk

import theme


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget: tk.Text, **kwargs):
        kwargs.setdefault("width", 48)
        kwargs.setdefault("bg", theme.BG_EDITOR_GUTTER)
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(master, **kwargs)
        self.text_widget = text_widget

    def redraw(self, *_args):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline_info = self.text_widget.dlineinfo(i)
            if dline_info is None:
                break
            y = dline_info[1]
            line_num = str(i).split(".")[0]
            self.create_text(
                38, y, anchor="ne", text=line_num,
                fill=theme.FG_GUTTER, font=(theme.FONT_FAMILY_MONO, 11),
            )
            i = self.text_widget.index(f"{i}+1line")
