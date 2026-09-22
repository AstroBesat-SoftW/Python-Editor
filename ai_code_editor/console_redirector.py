"""
console_redirector.py
----------------------
Redirects stdout/stderr into the console Text widget so that output from
user-executed code is displayed inside the application instead of a
terminal window. Supports colour-tagging so errors stand out visually.
"""

import tkinter as tk


class ConsoleRedirector:
    """A minimal, robust stdout/stderr-compatible writer for a Tk Text widget."""

    def __init__(self, text_widget: tk.Text, tag: str = "stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, message: str):
        if not message:
            return
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, message, self.tag)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        # Required for file-like objects; no buffering to flush.
        pass
