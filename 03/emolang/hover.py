import tkinter as tk
from emolang.src.tokens import TokenType
from emolang_lsp import get_tokens, hover_content


class HoverMixin:
    def _find_token_at(self, line, col):
        try:
            code = self.code_text.get("1.0", tk.END)
            lines = code.split("\n")
            tokens = get_tokens(code)
            for tok in tokens:
                if tok.type == TokenType.TOK_EOF:
                    continue
                line_text = lines[tok.line - 1] if tok.line - 1 < len(lines) else ""
                tc = self._tcl_col(line_text, tok.col)
                token_src = line_text[tok.col - 1 : tok.col - 1 + tok.char_length]
                te = tc + sum(2 if ord(c) > 0xFFFF else 1 for c in token_src)
                if tok.line == line and tc <= col < te:
                    return tok
        except RuntimeError:
            pass
        return None

    def on_mouse_move(self, event):
        self.code_text.tag_remove("hover_tag", "1.0", tk.END)
        if self._hover_tooltip:
            self._hover_tooltip.destroy()
            self._hover_tooltip = None
        if self._hover_timer_id:
            self.root.after_cancel(self._hover_timer_id)
            self._hover_timer_id = None

        index = self.code_text.index(f"@{event.x},{event.y}")
        if not index:
            return
        line = int(index.split(".")[0])
        col = int(index.split(".")[1])

        tok = self._find_token_at(line, col)
        if tok:
            code = self.code_text.get("1.0", tk.END)
            lines = code.split("\n")
            line_text = lines[tok.line - 1] if tok.line - 1 < len(lines) else ""
            tc = self._tcl_col(line_text, tok.col)
            token_src = line_text[tok.col - 1 : tok.col - 1 + tok.char_length]
            te = tc + sum(2 if ord(c) > 0xFFFF else 1 for c in token_src)
            self.code_text.tag_add("hover_tag", f"{line}.{tc}", f"{line}.{te}")

            self._hover_timer_id = self.root.after(
                400, lambda t=tok, e=event: self._show_hover_tooltip(t, e))

    def _show_hover_tooltip(self, tok, event):
        self._hover_timer_id = None
        content = hover_content(tok)
        self._hover_tooltip = tk.Toplevel(self.root)
        self._hover_tooltip.overrideredirect(True)
        self._hover_tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
        label = tk.Label(self._hover_tooltip, text=content,
                       font=("Consolas", 9), bg="#ffffcc", fg="#333",
                       padx=6, pady=4, relief=tk.SOLID, bd=1)
        label.pack()

    def _on_mouse_leave(self, event):
        if self._hover_timer_id:
            self.root.after_cancel(self._hover_timer_id)
            self._hover_timer_id = None
        if self._hover_tooltip:
            self._hover_tooltip.destroy()
            self._hover_tooltip = None
        self.code_text.tag_remove("hover_tag", "1.0", tk.END)
