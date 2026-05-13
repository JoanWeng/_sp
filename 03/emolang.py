#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'emolang', 'src'))

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

from tokens import TokenType
from ast import ASTType
from runtime import Value
from evaluator import EmoLangEvaluator


def run_cli(code):
    def input_callback():
        return input()

    interpreter = EmoLangEvaluator()
    try:
        output = interpreter.run(code, input_callback)
        print(output)
    except Exception as e:
        print(f"錯誤: {e}")


if HAS_TKINTER:
    class EmoLangGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("EmoLang 直譯器 v4.0")
            self.root.geometry("900x700")

            self.interpreter = EmoLangEvaluator()

            self.create_widgets()

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

            paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            paned.pack(fill=tk.BOTH, expand=True)

            left_frame = tk.Frame(paned, bg="#ecf0f1")
            paned.add(left_frame, width=450)

            code_label = tk.Label(left_frame, text="📝 程式碼", font=("Arial", 12, "bold"), bg="#ecf0f1")
            code_label.pack(anchor=tk.W, padx=10, pady=5)

            self.code_text = scrolledtext.ScrolledText(left_frame, font=("Consolas", 11),
                                                bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
            self.code_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            right_frame = tk.Frame(paned, bg="#ecf0f1")
            paned.add(right_frame, width=450)

            output_label = tk.Label(right_frame, text="📢 輸出結果", font=("Arial", 12, "bold"), bg="#ecf0f1")
            output_label.pack(anchor=tk.W, padx=10, pady=5)

            self.output_text = scrolledtext.ScrolledText(right_frame, font=("Consolas", 11),
                                                bg="#f8f9fa", fg="#2c3e50")
            self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            self.input_dialog = None

        def new_file(self):
            self.code_text.delete(1.0, tk.END)
            self.output_text.delete(1.0, tk.END)

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

        def clear_output(self):
            self.output_text.delete(1.0, tk.END)


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