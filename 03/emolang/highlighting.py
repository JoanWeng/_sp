import sys
import tkinter as tk
from emolang.src.lexer import EmoLangLexer
from emolang.src.parser import EmoLangParser
from emolang.src.tokens import TokenType
from emolang_lsp import get_tokens, get_semantic_tag
from emolang.constants import SEMANTIC_TAG_MAP


class HighlightingMixin:
    def _reconstruct_full_code(self):
        """Replace fold markers with original text to get the full source for diagnostics."""
        code = self.code_text.get("1.0", tk.END)
        if not self._folded_regions:
            return code
        lines = code.split("\n")
        for text, marker in self._folded_regions:
            for i, line in enumerate(lines):
                if marker in line:
                    original_lines = text.split("\n")
                    lines[i:i+1] = original_lines
                    break
        return "\n".join(lines)

    def _apply_semantic_highlighting(self):
        code = self.code_text.get("1.0", tk.END)
        for name in SEMANTIC_TAG_MAP:
            self.code_text.tag_remove(name, "1.0", tk.END)
        self.code_text.tag_remove("hover_tag", "1.0", tk.END)
        self.code_text.tag_remove("error_tag", "1.0", tk.END)

        try:
            lines = code.split("\n")

            self._all_errors = []
            diag_code = self._reconstruct_full_code()
            lexer = EmoLangLexer(diag_code)
            parser = EmoLangParser(lexer)
            parser.diag_parse()
            seen_lines = set()
            for rel_line, msg in parser.diag_errors:
                if rel_line > 0 and rel_line not in seen_lines and len(self._all_errors) < 100:
                    seen_lines.add(rel_line)
                    self._all_errors.append((rel_line, msg))

            for err_line, _ in self._all_errors:
                if err_line > 0 and err_line <= len(lines):
                    try:
                        self.code_text.tag_add("error_tag", f"{err_line}.0", f"{err_line}.0 lineend")
                    except tk.TclError:
                        pass

            if self._all_errors:
                count = len(self._all_errors)
                if count == 1:
                    self._error_msg = self._all_errors[0][1]
                else:
                    self._error_msg = f"⚠ 發現 {count} 個語法錯誤: " + "; ".join(msg for _, msg in self._all_errors[:3])
                    if count > 3:
                        self._error_msg += " ..."
            else:
                self._error_msg = None
            self._update_error_label()

            try:
                tokens = get_tokens(code)
            except RuntimeError:
                tokens = []

            for tok in tokens:
                if tok.type == TokenType.TOK_EOF:
                    continue
                tag = get_semantic_tag(tok, None)
                if tok.line <= 0 or tok.line > len(lines):
                    continue
                line_text = lines[tok.line - 1]
                if tok.col <= 0 or tok.col > len(line_text):
                    continue
                tc = self._tcl_col(line_text, tok.col)
                end_idx = tok.col - 1 + max(tok.char_length, 1)
                token_src = line_text[tok.col - 1 : end_idx]
                if not token_src:
                    continue
                tcl_end = tc + sum(2 if ord(c) > 0xFFFF else 1 for c in token_src)
                try:
                    self.code_text.tag_add(tag, f"{tok.line}.{tc}", f"{tok.line}.{tcl_end}")
                except tk.TclError:
                    pass
        except Exception as e:
            msg = f"[HL error] {e}"
            print(msg, file=sys.stderr)
            self._debug_label.config(text=msg)
            self._update_error_label()

    def _update_error_label(self):
        if hasattr(self, '_all_errors') and self._all_errors:
            count = len(self._all_errors)
            if count == 1:
                self._error_label.config(text=f"⚠ {self._all_errors[0][1]}", fg="#f44747")
            else:
                self._error_label.config(text=f"⚠ 發現 {count} 個語法錯誤", fg="#f44747")
        elif self._error_msg:
            self._error_label.config(text=f"⚠ {self._error_msg}", fg="#f44747")
        else:
            self._error_label.config(text="✔ 無語法錯誤", fg="#6a9955")

    def _show_diagnostics(self):
        errors = getattr(self, '_all_errors', [])
        if not errors and self._error_msg:
            errors = [(0, self._error_msg)]

        win = tk.Toplevel(self.root)
        win.title("⚠ 診斷結果")
        win.geometry("500x300")
        win.configure(bg="#252526")
        label = tk.Label(win, text=f"找到 {len(errors)} 個錯誤",
                         bg="#252526", fg="#cccccc", font=("Arial", 10))
        label.pack(pady=(10, 0))
        lb = tk.Listbox(win, bg="#1e1e1e", fg="#e06c75",
                        font=("Consolas", 10), selectbackground="#264f78")
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for line, msg in errors:
            lb.insert(tk.END, f"  line {line}: {msg}")

        def on_select(ev):
            sel = lb.curselection()
            if sel and sel[0] < len(errors):
                line = errors[sel[0]][0]
                if line > 0:
                    self.code_text.see(f"{line}.0")
                    self.code_text.mark_set(tk.INSERT, f"{line}.0")
                    self.code_text.focus_set()
                    win.destroy()
        if errors:
            lb.bind("<<ListboxSelect>>", on_select)
