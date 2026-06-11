import tkinter as tk
from emolang.src.lexer import EmoLangLexer
from emolang.src.parser import EmoLangParser


class OutlineMixin:
    def _schedule_outline_update(self):
        if self._outline_timer_id:
            self.root.after_cancel(self._outline_timer_id)
        self._outline_timer_id = self.root.after(500, self._do_update_outline)

    def _do_update_outline(self):
        self._outline_timer_id = None
        try:
            self.outline_listbox.delete(0, tk.END)
            self._outline_lines.clear()
            code = self.code_text.get("1.0", tk.END)
            if getattr(self, '_folded_regions', None):
                code = self._reconstruct_full_code()
            lexer = EmoLangLexer(code)
            parser = EmoLangParser(lexer)
            nodes = parser.diag_parse()
            for node in nodes:
                self._add_outline_node(node, 0)
        except Exception:
            pass

    def _add_outline_node(self, node, depth):
        icons = {"FUNC_DEF": "🛠️", "LET": "📦", "STRUCT_DEF": "🏗️", "VAR": "📦"}
        name = getattr(node, "name", None)
        if not name or node.type not in icons:
            return
        indent = "  " * depth
        self.outline_listbox.insert(tk.END, f"{indent}{icons[node.type]} {name}")
        self._outline_lines.append(node.line)
        if node.type == "FUNC_DEF":
            for p in (node.left or []):
                self._add_outline_node(p, depth + 1)
            for s in (node.body or []):
                self._add_outline_node(s, depth + 1)
        elif node.type == "STRUCT_DEF":
            for s in (node.body or []):
                self._add_outline_node(s, depth + 1)

    def _on_outline_select(self, event):
        sel = self.outline_listbox.curselection()
        if sel and sel[0] < len(self._outline_lines):
            try:
                line = self._outline_lines[sel[0]]
                self.code_text.see(f"{line}.0")
                self.code_text.mark_set(tk.INSERT, f"{line}.0")
                self.code_text.focus_set()
            except Exception:
                pass
