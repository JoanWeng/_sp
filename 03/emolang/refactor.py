import tkinter as tk
from tkinter import simpledialog, messagebox
from emolang.src.tokens import TokenType
from emolang_lsp import get_tokens


class RefactorMixin:
    def _get_all_id_tokens(self):
        code = self.code_text.get("1.0", tk.END)
        tokens = get_tokens(code)
        id_tokens = {}
        for tok in tokens:
            if tok.type == TokenType.TOK_ID:
                id_tokens.setdefault(tok.value, []).append(tok)
        return id_tokens

    def _show_references(self, event=None):
        try:
            cursor = self.code_text.index(tk.INSERT)
            line = int(cursor.split(".")[0])
            col = int(cursor.split(".")[1])
            tok = self._find_token_at(line, col)
            if not tok or tok.type != TokenType.TOK_ID:
                self._debug_label.config(text="Ctrl+Shift+F: 游標不在識別字上")
                return None
            id_tokens = self._get_all_id_tokens()
            refs = id_tokens.get(tok.value, [])
            if not refs:
                self._debug_label.config(text=f"'{tok.value}': 無任何參照")
                return None
            win = tk.Toplevel(self.root)
            win.title(f"參照: {tok.value}")
            win.geometry("400x250")
            win.configure(bg="#252526")
            lb = tk.Listbox(win, bg="#1e1e1e", fg="#d4d4d4",
                            font=("Consolas", 10), selectbackground="#264f78")
            lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            for t in refs:
                lb.insert(tk.END, f"  line {t.line}:{t.col}  {t.value}")

            def on_select(ev):
                sel = lb.curselection()
                if sel:
                    t = refs[sel[0]]
                    lines = self.code_text.get("1.0", tk.END).split("\n")
                    line_text = lines[t.line - 1] if t.line - 1 < len(lines) else ""
                    tc = self._tcl_col(line_text, t.col)
                    self.code_text.see(f"{t.line}.{tc}")
                    self.code_text.mark_set(tk.INSERT, f"{t.line}.{tc}")
                    self.code_text.focus_set()
                    win.destroy()
            lb.bind("<<ListboxSelect>>", on_select)
            self._debug_label.config(text=f"Ctrl+Shift+F: '{tok.value}' → {len(refs)} 個參照")
            return "break"
        except Exception as e:
            self._debug_label.config(text=f"references error: {e}")
            return None

    def _rename_symbol(self, event=None):
        try:
            cursor = self.code_text.index(tk.INSERT)
            line = int(cursor.split(".")[0])
            col = int(cursor.split(".")[1])
            tok = self._find_token_at(line, col)
            if not tok or tok.type != TokenType.TOK_ID:
                self._debug_label.config(text="F2: 游標不在識別字上")
                return None
            new_name = simpledialog.askstring(
                "重新命名", f"將「{tok.value}」重新命名為：",
                parent=self.root, initialvalue=tok.value)
            if not new_name or new_name == tok.value:
                return None
            if new_name:
                if new_name[0].isdigit():
                    messagebox.showerror("錯誤", "識別字不能以數字開頭", parent=self.root)
                    return None
                if not new_name[0].isalpha() and new_name[0] != '_':
                    messagebox.showerror("錯誤", f"識別字不能以特殊符號開頭 ({new_name[0]})", parent=self.root)
                    return None
            id_tokens = self._get_all_id_tokens()
            refs = id_tokens.get(tok.value, [])
            if not refs:
                return None
            if self._folded_regions:
                self._unfold_all()
            old_code = self.code_text.get("1.0", tk.END)
            lines = old_code.split("\n")
            for t in reversed(refs):
                col = t.col - 1
                old = lines[t.line - 1]
                lines[t.line - 1] = old[:col] + new_name + old[col + len(t.value):]
            new_code = "\n".join(lines)
            self.code_text.replace("1.0", tk.END, new_code)
            self._apply_semantic_highlighting()
            self._schedule_outline_update()
            self._update_line_numbers()
            self._debug_label.config(text=f"F2: '{tok.value}' → '{new_name}' ({len(refs)} 處)")
            return "break"
        except Exception as e:
            self._debug_label.config(text=f"rename error: {e}")
            return None
