import tkinter as tk


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self.enter)
        widget.bind('<Leave>', self.leave)

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.geometry(f"+{int(x)}+{int(y)}")
        label = tk.Label(self.tip, text=self.text, font=("Consolas", 9),
                         bg="#ffffcc", fg="#333333", padx=6, pady=2, relief=tk.SOLID, bd=1)
        label.pack()

    def leave(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class GhostText:
    def __init__(self, text_widget):
        self.text = text_widget
        self.label = None
        self.text_content = ''

    def show(self, content):
        self.hide()
        if not content:
            return
        self.text_content = content
        cursor = self.text.index(tk.INSERT)
        bbox = self.text.bbox(cursor)
        if not bbox:
            return
        self.label = tk.Label(
            self.text, text=content, font=("Consolas", 11),
            fg="#555555", bg="#1e1e1e", anchor=tk.W,
        )
        self.label.place(x=bbox[0], y=bbox[1])

    def hide(self):
        self.text_content = ''
        if self.label is not None:
            self.label.place_forget()
            self.label = None
