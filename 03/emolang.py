#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'emolang', 'src'))

try:
    import tkinter as tk
    from tkinter import scrolledtext, filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

from evaluator import EmoLangEvaluator
from completion import CompletionEngine
from emolang.widgets import ToolTip, GhostText


def run_cli(code):
    def input_callback():
        return input()

    interpreter = EmoLangEvaluator()
    try:
        output = interpreter.run(code, input_callback)
        print(output)
    except Exception as e:
        print(f"錯誤: {e}")


EMOJI_NAMES = {
    "📦": "LET 通用變數（void*，可裝載任何型態）",
    "🔢": "INT 整數變數（int）",
    "🎈": "FLOAT 小數變數（float）",
    "📝": "STR 字串變數（str）",
    "🚦": "BOOL 布林變數（bool）",
    "🟰": "ASSIGN 賦值（=）",
    "📢": "PRINT 輸出值到畫面",
    "📥": "INPUT 讀取使用者輸入",
    "🤔": "IF 條件判斷",
    "🤷": "ELSE 否則分支",
    "🔁": "WHILE 條件迴圈",
    "🎡": "FOR 計數迴圈",
    "🚧": "SEP For 迴圈分隔符",
    "👇": "LBRACE 區塊開始 {",
    "👆": "RBRACE 區塊結束 }",
    "🛠️": "FUNC 定義函數",
    "🔙": "RETURN 從函數回傳值",
    "🏗️": "STRUCT 定義結構體",
    "🆕": "NEW 建立實例（struct/list/dict）",
    "➡️": "DOT 存取成員欄位（obj.field）",
    "➕": "PLUS 加法或字串拼接（+）",
    "➖": "MINUS 減法（-）",
    "✖️": "MUL 乘法（*）",
    "➗": "DIV 除法（/）",
    "✂️": "MOD 取餘數（%）",
    "🤝": "EQ 等於比較（==）",
    "📈": "GT 大於（>）",
    "📉": "LT 小於（<）",
    "🔗": "AND 邏輯 AND（&&）",
    "🔀": "OR 邏輯 OR（||）",
    "🙅": "NOT 邏輯 NOT（!）",
    "📍": "REF 取變數位址（&）",
    "🎯": "DEREF 解參考取得值（*）",
    "📌": "INDEX 索引存取（arr[i]）",
    "📚": "ARRAY 配置連續記憶體",
    "📋": "LIST 建立空白列表",
    "📖": "DICT 建立空白字典",
    "🛒": "APPEND 追加元素到列表尾端",
    "📏": "LEN 計算長度",
    "🟢": "TRUE 真值（1）",
    "🔴": "FALSE 假值（0）",
}


if HAS_TKINTER:
    class EmoLangGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("EmoLang 直譯器 v4.0")
            self.root.geometry("900x700")

            self.interpreter = EmoLangEvaluator()
            self.next_line_suggestion = None
            self._suggestion_timer = None

            self.create_widgets()
            self.ghost = GhostText(self.code_text)

        def create_widgets(self):
            title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
            title_frame.pack(fill=tk.X)
            title_frame.pack_propagate(False)

            title_label = tk.Label(title_frame, text="EmoLang 直譯器",
                                font=("Arial", 20, "bold"), bg="#2c3e50", fg="#ecf0f1")
            title_label.pack(pady=15)

            toolbar = tk.Frame(self.root, bg="#34495e")
            toolbar.pack(fill=tk.X)

            btn_new = tk.Button(toolbar, text="📄 新建", command=self.new_file, bg="#3498db", fg="white")
            btn_new.pack(side=tk.LEFT, padx=5, pady=5)

            btn_open = tk.Button(toolbar, text="📂 開啟", command=self.open_file, bg="#3498db", fg="white")
            btn_open.pack(side=tk.LEFT, padx=5, pady=5)

            btn_save = tk.Button(toolbar, text="💾 儲存", command=self.save_file, bg="#3498db", fg="white")
            btn_save.pack(side=tk.LEFT, padx=5, pady=5)

            btn_run = tk.Button(toolbar, text="▶ 執行", command=self.run_code, bg="#27ae60", fg="white", font=("Arial", 10, "bold"))
            btn_run.pack(side=tk.LEFT, padx=20, pady=5)

            btn_clear = tk.Button(toolbar, text="🗑️ 清除", command=self.clear_output, bg="#e74c3c", fg="white")
            btn_clear.pack(side=tk.LEFT, padx=5, pady=5)

            self.emoji_toggle = tk.Button(toolbar, text="🔣", command=self.toggle_emoji,
                                           bg="#8e44ad", fg="white", font=("Arial", 10), width=3)
            self.emoji_toggle.pack(side=tk.RIGHT, padx=5, pady=5)

            self.emoji_frame = tk.Frame(self.root, bg="#2c3e50")

            categories = [
                ["📦", "📝", "🔢", "🎈", "🚦", "🟰"],
                ["📢", "📥", "🤔", "🤷", "🔁", "🎡", "🚧"],
                ["👇", "👆", "🛠️", "🔙", "🏗️", "🆕", "➡️"],
                ["➕", "➖", "✖️", "➗", "✂️", "🤝", "📈", "📉"],
                ["🔗", "🔀", "🙅", "📍", "🎯", "📌", "📚"],
                ["📋", "📖", "🛒", "📏", "🟢", "🔴"],
            ]
            for emojis in categories:
                row = tk.Frame(self.emoji_frame, bg="#2c3e50")
                row.pack(fill=tk.X, padx=8, pady=1)
                for emoji in emojis:
                    btn = tk.Button(row, text=emoji, font=("Segoe UI Emoji", 12),
                                  bg="#34495e", fg="white", relief=tk.RIDGE,
                                  bd=1, width=2, padx=3, pady=1,
                                  command=lambda e=emoji: self.insert_emoji(e))
                    btn.pack(side=tk.LEFT, padx=2, pady=1)
                    name = EMOJI_NAMES.get(emoji, "")
                    if name:
                        ToolTip(btn, name)

            self.emoji_visible = False

            self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            self.paned.pack(fill=tk.BOTH, expand=True)

            left_frame = tk.Frame(self.paned, bg="#ecf0f1")
            self.paned.add(left_frame, width=450)

            code_label = tk.Label(left_frame, text="📝 程式碼", font=("Arial", 12, "bold"), bg="#ecf0f1")
            code_label.pack(anchor=tk.W, padx=10, pady=5)

            self.code_text = scrolledtext.ScrolledText(left_frame, font=("Consolas", 11),
                                                bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
            self.code_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            self.code_text.bind('<KeyRelease>', self.on_key_release)
            self.code_text.bind('<Return>', self.on_enter)
            self.code_text.bind('<Tab>', self.on_tab)

            self.suggestion_bar = tk.Label(left_frame, text="", font=("Consolas", 10),
                                           bg="#2c3e50", fg="#95a5a6", anchor=tk.W, height=1)
            self.suggestion_bar.pack(fill=tk.X, padx=10, pady=(0, 5))

            right_frame = tk.Frame(self.paned, bg="#ecf0f1")
            self.paned.add(right_frame, width=450)

            output_label = tk.Label(right_frame, text="📢 輸出結果", font=("Arial", 12, "bold"), bg="#ecf0f1")
            output_label.pack(anchor=tk.W, padx=10, pady=5)

            self.output_text = scrolledtext.ScrolledText(right_frame, font=("Consolas", 11),
                                                bg="#f8f9fa", fg="#2c3e50", state='disabled')
            self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            self.input_dialog = None

        def new_file(self):
            self.code_text.delete(1.0, tk.END)
            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state='disabled')

        def open_file(self):
            filename = filedialog.askopenfilename(filetypes=[("EmoLang 檔案", "*.emo"), ("文字檔", "*.txt"), ("所有檔案", "*.*")])
            if filename:
                with open(filename, "r", encoding="utf-8") as f:
                    self.code_text.delete(1.0, tk.END)
                    self.code_text.insert(1.0, f.read())

        def save_file(self):
            filename = filedialog.asksaveasfilename(defaultextension=".emo",
                                                filetypes=[("EmoLang 檔案", "*.emo"), ("文字檔", "*.txt")])
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.code_text.get(1.0, tk.END))

        def run_code(self):
            code = self.code_text.get(1.0, tk.END).strip()
            if not code:
                return

            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)

            def input_callback():
                self.input_dialog = tk.Toplevel(self.root)
                self.input_dialog.title("輸入")
                self.input_dialog.geometry("300x100")

                label = tk.Label(self.input_dialog, text="請輸入：")
                label.pack(pady=10)

                entry = tk.Entry(self.input_dialog)
                entry.pack(pady=5)
                entry.focus()

                result = [None]

                def on_submit():
                    result[0] = entry.get()
                    self.input_dialog.destroy()

                btn_ok = tk.Button(self.input_dialog, text="確定", command=on_submit)
                btn_ok.pack(pady=5)

                self.input_dialog.wait_window()
                return result[0] if result[0] else ""

            try:
                output = self.interpreter.run(code, input_callback)
                self.output_text.insert(1.0, output)
            except Exception as e:
                self.output_text.insert(1.0, f"錯誤: {str(e)}")
            finally:
                self.output_text.config(state='disabled')

        def clear_output(self):
            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state='disabled')
            self.output_text.update_idletasks()

        def toggle_emoji(self):
            if self.emoji_visible:
                self.emoji_frame.pack_forget()
                self.emoji_visible = False
            else:
                self.emoji_frame.pack(fill=tk.X, before=self.paned)
                self.emoji_visible = True

        def insert_emoji(self, emoji):
            self.code_text.insert(tk.INSERT, emoji)
            self.code_text.focus_set()
            self.remove_ghost()
            self.next_line_suggestion = None
            self.suggestion_bar.config(text="")
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
            self.suggestion_bar.config(text="")

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
                    self.suggestion_bar.config(text=f"Tab: {next_sug}")

        def on_key_release(self, event):
            if self._suggestion_timer:
                self.root.after_cancel(self._suggestion_timer)
                self._suggestion_timer = None

            self.remove_ghost()

            if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                                'Alt_L', 'Alt_R', 'Up', 'Down', 'Left', 'Right',
                                'Escape', 'Return', 'Tab'):
                self.next_line_suggestion = None
                self.suggestion_bar.config(text="")
                return

            self._suggestion_timer = self.root.after(80, self.update_suggestion)

        def on_enter(self, event):
            return None

        def on_tab(self, event):
            self.update_suggestion()

            if self.ghost.label is not None and self.ghost.text_content:
                self.code_text.insert(tk.INSERT, self.ghost.text_content)
                self.remove_ghost()
                self.suggestion_bar.config(text="")
                return 'break'

            if self.next_line_suggestion:
                self.code_text.insert(tk.INSERT, self.next_line_suggestion)
                self.next_line_suggestion = None
                self.suggestion_bar.config(text="")
                return 'break'

            self.code_text.insert(tk.INSERT, '    ')
            return 'break'

        def on_up(self, event):
            pass

        def on_down(self, event):
            pass


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "-i" or sys.argv[1] == "--interactive":
            if not HAS_TKINTER:
                print("錯誤: 此環境未安裝 Tkinter")
                sys.exit(1)
            root = tk.Tk()
            app = EmoLangGUI(root)
            root.mainloop()
        else:
            filename = sys.argv[1]
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    code = f.read()
                run_cli(code)
            except FileNotFoundError:
                print(f"找不到檔案: {filename}")
            except Exception as e:
                print(f"錯誤: {e}")
    else:
        if HAS_TKINTER:
            root = tk.Tk()
            app = EmoLangGUI(root)
            root.mainloop()
        else:
            print("用法: python emolang.py <filename.emo>")
            print("   或: python emolang.py -i     (使用互動模式)")
            print("")
            print("錯誤: 此環境未安裝 Tkinter，無法使用 GUI")
            sys.exit(1)


if __name__ == "__main__":
    main()
