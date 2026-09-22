"""
main.py
-------
Entry point for Sotstech Python Editor.

Run with:
    python main.py
"""

import sys
import traceback
import tkinter as tk
from tkinter import messagebox

from editor_app import AICodeStudio


def main():
    root = tk.Tk()
    try:
        AICodeStudio(root)
    except Exception as exc:  # noqa: BLE001 - never let startup crash silently
        traceback.print_exc()
        try:
            messagebox.showerror(
                "Startup Error",
                f"Sotstech Python Editor failed to start:\n{exc}",
            )
        except Exception:
            pass
        return
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - absolute last line of defense
        traceback.print_exc(file=sys.stderr)
