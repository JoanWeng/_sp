import tkinter as tk
from emolang.src.completion import CompletionEngine


class SuggestionsMixin:
    def insert_emoji(self, emoji):
        self.code_text.edit_separator()
        self.code_text.insert(tk.INSERT, emoji)
        self.code_text.edit_separator()
        self.code_text.focus_set()
        self.remove_ghost()
        self.next_line_suggestion = None
        self._apply_semantic_highlighting()
        self._schedule_outline_update()
        self._update_line_numbers()
        self.root.after(80, self.update_suggestion)

    def remove_ghost(self):
        self.ghost.hide()

    def show_ghost(self, text):
        self.ghost.show(text)

    def update_suggestion(self):
        cursor = self.code_text.index(tk.INSERT)
        cursor_line = int(cursor.split('.')[0])
        cursor_col = int(cursor.split('.')[1])
        all_text = self.code_text.get('1.0', tk.END)
        all_lines = all_text.split('\n')
        line_text = all_lines[cursor_line - 1] if cursor_line <= len(all_lines) else ""

        self.remove_ghost()
        self.next_line_suggestion = None

        line_sug = CompletionEngine.get_line_suggestion(line_text)
        if line_sug:
            self.show_ghost(line_sug)
            return

        stripped = line_text.strip()
        if stripped:
            var_ghost = CompletionEngine.get_variable_ghost(line_text, cursor_col, all_text)
            if var_ghost:
                self.show_ghost(var_ghost)
                return

        if not stripped:
            next_sug = CompletionEngine.get_next_line_suggestion(all_lines, cursor_line - 1)
            if next_sug:
                self.next_line_suggestion = '\n' + next_sug

    def on_key_release(self, event):
        if self._suggestion_timer:
            self.root.after_cancel(self._suggestion_timer)
            self._suggestion_timer = None

        self.remove_ghost()

        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                            'Alt_L', 'Alt_R', 'Up', 'Down', 'Left', 'Right',
                            'Escape', 'Return', 'Tab'):
            self.next_line_suggestion = None
            return

        self._suggestion_timer = self.root.after(80, self.update_suggestion)
        self._apply_semantic_highlighting()
        self._schedule_outline_update()
        self._update_line_numbers()

    def on_enter(self, event):
        return None

    def on_tab(self, event):
        self.update_suggestion()

        if self.ghost.label is not None and self.ghost.text_content:
            self.code_text.insert(tk.INSERT, self.ghost.text_content)
            self.remove_ghost()
            return 'break'

        if self.next_line_suggestion:
            self.code_text.insert(tk.INSERT, self.next_line_suggestion)
            self.next_line_suggestion = None
            return 'break'

        self.code_text.insert(tk.INSERT, '    ')
        return 'break'

    def on_up(self, event):
        pass

    def on_down(self, event):
        pass
