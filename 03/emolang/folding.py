import sys
import tkinter as tk
from emolang_lsp import get_tokens
from emolang.src.tokens import TokenType


class FoldingMixin:
    def _get_folding_ranges(self):
        code = self.code_text.get("1.0", tk.END)
        tokens = get_tokens(code)
        lines = code.split("\n")
        brace_stack = []
        ranges = []
        for tok in tokens:
            if tok.type == TokenType.TOK_LBRACE:
                brace_stack.append(tok.line)
            elif tok.type == TokenType.TOK_RBRACE:
                if 0 <= tok.line - 1 < len(lines) and "[#" in lines[tok.line - 1]:
                    if brace_stack:
                        brace_stack.pop()
                    continue
                if brace_stack:
                    start = brace_stack.pop()
                    end = tok.line
                    if not brace_stack and end > start:
                        ranges.append((start, end))
        return ranges

    def _fold_all(self, event=None):
        if self._folded_regions:
            self._unfold_all()
        self.code_text.config(undo=False)
        try:
            ranges = self._get_folding_ranges()
            ranges.sort(key=lambda r: r[0], reverse=True)
            folded = []
            for start, end in ranges:
                idx = f"{start+1}.0"
                end_idx = f"{end+1}.0"
                text = self.code_text.get(idx, end_idx)
                if text.strip():
                    self.code_text.delete(idx, end_idx)
                    uid = id(text) & 0xFFFF
                    marker = f"  … 👆 ({end-start} lines) [#{uid:04x}]  \n"
                    self.code_text.insert(idx, marker)
                    self.code_text.tag_add("fold_marker", idx, f"{int(idx.split('.')[0])+1}.0")
                    folded.append((text, marker.rstrip()))
        finally:
            self.code_text.edit_reset()
            self.code_text.config(undo=True)
        self._folded_regions = folded
        if folded:
            self._debug_label.config(text=f"📂 已摺疊 {len(folded)} 個區塊，按「展開」或點擊標記還原")
        self._apply_semantic_highlighting()
        self._update_line_numbers()

    def _unfold_all(self, event=None):
        had_folded = bool(self._folded_regions)
        self.code_text.config(undo=False)
        try:
            for text, marker in self._folded_regions:
                try:
                    pos = self.code_text.search(marker, tk.END, backwards=True)
                    if pos:
                        line = int(pos.split(".")[0])
                        self.code_text.delete(f"{line}.0", f"{line+1}.0")
                        self.code_text.insert(f"{line}.0", text)
                except tk.TclError:
                    pass
        finally:
            self.code_text.edit_reset()
            self.code_text.config(undo=True)
        self._folded_regions = []
        self.code_text.tag_remove("fold_marker", "1.0", tk.END)
        self._apply_semantic_highlighting()
        if had_folded:
            self._debug_label.config(text="📂 已展開全部區塊")
        self._update_line_numbers()

    def _unfold_marker_at_line(self, line):
        for i, (text, marker) in enumerate(self._folded_regions):
            pos = self.code_text.search(marker, f"{line}.0", f"{line+1}.0")
            if pos:
                self.code_text.config(undo=False)
                try:
                    self.code_text.delete(f"{line}.0", f"{line+1}.0")
                    self.code_text.insert(f"{line}.0", text)
                except tk.TclError:
                    self.code_text.config(undo=True)
                    return False
                self.code_text.edit_reset()
                self.code_text.config(undo=True)
                self._folded_regions.pop(i)
                self._apply_semantic_highlighting()
                try:
                    self.code_text.tag_remove("fold_marker", "1.0", tk.END)
                    for _, m in self._folded_regions:
                        p = self.code_text.search(m, tk.END, backwards=True)
                        if p:
                            pl = int(p.split(".")[0])
                            self.code_text.tag_add("fold_marker", f"{pl}.0", f"{pl+1}.0")
                except tk.TclError:
                    pass
                self._update_line_numbers()
                return True
        return False

    def _on_fold_click(self, event):
        try:
            index = self.code_text.index(f"@{event.x},{event.y}")
            if index:
                line = int(index.split(".")[0])
                if self._unfold_marker_at_line(line):
                    self._debug_label.config(text=f"📂 已展開 line {line}")
        except Exception as e:
            print(f"[fold click error] {e}", file=sys.stderr)
            self._debug_label.config(text=f"⚠ 展開失敗: {e}")
        return "break"
