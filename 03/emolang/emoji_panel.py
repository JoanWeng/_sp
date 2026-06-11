import json
import os
import tkinter as tk
from emolang.constants import EMOJI_NAMES, EMOJI_KEY_CONFIG_FILE, DEFAULT_EMOJI_KEY_MAP


class EmojiMixin:
    def toggle_emoji(self):
        if self.emoji_visible:
            self.emoji_frame.pack_forget()
            self.emoji_visible = False
        else:
            self.emoji_frame.pack(fill=tk.X, before=self.paned)
            self.emoji_visible = True

    def toggle_emoji_key_mode(self):
        self._emoji_key_mode = not self._emoji_key_mode
        if self._emoji_key_mode:
            self.key_mode_btn.config(text="🔣 模式", bg="#8e44ad")
            self.code_text.focus_set()
        else:
            self.key_mode_btn.config(text="⌨️ 模式", bg="#2c3e50")

    def _load_emoji_key_map(self):
        try:
            if os.path.exists(EMOJI_KEY_CONFIG_FILE):
                with open(EMOJI_KEY_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._emoji_key_map = {k.lower(): v for k, v in data.items() if len(k) == 1}
                return
        except (json.JSONDecodeError, OSError):
            pass
        self._emoji_key_map = dict(DEFAULT_EMOJI_KEY_MAP)

    def _save_emoji_key_map(self):
        try:
            with open(EMOJI_KEY_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._emoji_key_map, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _configure_emoji_keys(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("設定 Emoji 快捷鍵")
        dlg.geometry("520x400")
        dlg.configure(bg="#2c3e50")
        dlg.transient(self.root)
        dlg.grab_set()

        rev_map = {v: k for k, v in self._emoji_key_map.items()}

        def refresh_labels():
            nonlocal rev_map
            rev_map.clear()
            rev_map.update({v: k for k, v in self._emoji_key_map.items()})
            for emoji, lbl in key_labels.items():
                ch = rev_map.get(emoji, "")
                lbl.config(text=f"[{ch.upper()}]" if ch else "[-]",
                          bg="#3b5a70" if ch else "#555555")

        info = tk.Label(dlg, text="點選 emoji → 按鍵盤字母設定快捷鍵", bg="#2c3e50", fg="#ecf0f1",
                       font=("Arial", 10))
        info.pack(fill=tk.X, padx=10, pady=5)

        frame = tk.Frame(dlg, bg="#34495e")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(frame, bg="#34495e", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#34495e")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_canvas_wheel(event):
            if event.num == 4:
                canvas.yview_scroll(-3, "units")
            elif event.num == 5:
                canvas.yview_scroll(3, "units")
            else:
                canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
            return "break"
        canvas.bind("<MouseWheel>", _on_canvas_wheel)
        canvas.bind("<Button-4>", _on_canvas_wheel)
        canvas.bind("<Button-5>", _on_canvas_wheel)
        scroll_frame.bind("<MouseWheel>", _on_canvas_wheel)
        scroll_frame.bind("<Button-4>", _on_canvas_wheel)
        scroll_frame.bind("<Button-5>", _on_canvas_wheel)

        selected = tk.StringVar()
        key_labels = {}

        for emoji in EMOJI_NAMES:
            display_emoji = emoji.replace('\ufe0f', '')
            row_f = tk.Frame(scroll_frame, bg="#34495e")
            row_f.pack(fill=tk.X, padx=5, pady=2)

            rb = tk.Radiobutton(row_f, variable=selected, value=emoji, bg="#34495e",
                                fg="#ecf0f1", selectcolor="#2c3e50", activebackground="#34495e")
            rb.pack(side=tk.LEFT)

            btn = tk.Button(row_f, text=display_emoji, font=("Segoe UI Emoji", 14),
                          bg="#3b5a70", fg="white", relief=tk.RIDGE, bd=1, width=3,
                          command=lambda e=emoji: selected.set(e))
            btn.pack(side=tk.LEFT, padx=3)

            name = EMOJI_NAMES.get(emoji, "")
            tk.Label(row_f, text=name, bg="#34495e", fg="#cccccc",
                    font=("Consolas", 9), anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            key_ch = rev_map.get(emoji, "")
            lbl = tk.Label(row_f, text=f"[{key_ch.upper()}]" if key_ch else "[-]",
                          bg="#3b5a70" if key_ch else "#555555", fg="#f0f0f0",
                          font=("Consolas", 9, "bold"), width=5)
            lbl.pack(side=tk.RIGHT, padx=5)
            key_labels[emoji] = lbl

        def on_key(event):
            if selected.get() and event.char and event.char.isalpha():
                ch = event.char.lower()
                old_emoji = None
                for e, k in self._emoji_key_map.items():
                    if k == ch:
                        old_emoji = e
                        break
                if old_emoji:
                    del self._emoji_key_map[old_emoji]
                self._emoji_key_map[ch] = selected.get()
                self._save_emoji_key_map()
                refresh_labels()

        def clear_key():
            emoji = selected.get()
            if not emoji:
                return
            for k, v in list(self._emoji_key_map.items()):
                if v == emoji:
                    del self._emoji_key_map[k]
                    break
            self._save_emoji_key_map()
            refresh_labels()

        def reset_defaults():
            self._emoji_key_map = dict(DEFAULT_EMOJI_KEY_MAP)
            self._save_emoji_key_map()
            refresh_labels()

        dlg.bind("<KeyPress>", on_key)

        btn_frame = tk.Frame(dlg, bg="#2c3e50")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text="清除按鍵", command=clear_key,
                 bg="#c0392b", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="恢復預設", command=reset_defaults,
                 bg="#2c3e50", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="關閉", command=dlg.destroy,
                 bg="#3498db", fg="white", font=("Arial", 9)).pack(side=tk.RIGHT, padx=3)
