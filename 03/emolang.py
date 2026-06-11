#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    import tkinter as tk
    from tkinter import scrolledtext, filedialog, simpledialog, messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

from emolang.src.evaluator import EmoLangEvaluator
from emolang_lsp import highlight_ansi, ANSI_RESET

if HAS_TKINTER:
    from emolang.src.completion import CompletionEngine
    from emolang.widgets import ToolTip, GhostText
    from emolang.src.tokens import TokenType
    from emolang.src.lexer import EmoLangLexer
    from emolang.src.parser import EmoLangParser
    from emolang_lsp import get_tokens, get_semantic_tag, hover_content
    from emolang.constants import SEMANTIC_TAG_MAP, EMOJI_NAMES, EMOJI_KEY_CONFIG_FILE, DEFAULT_EMOJI_KEY_MAP
    from emolang.folding import FoldingMixin
    from emolang.highlighting import HighlightingMixin
    from emolang.outline import OutlineMixin
    from emolang.hover import HoverMixin
    from emolang.refactor import RefactorMixin
    from emolang.emoji_panel import EmojiMixin
    from emolang.suggestions import SuggestionsMixin


def run_cli(code):
    def input_callback():
        return input()

    interpreter = EmoLangEvaluator()
    try:
        output = interpreter.run(code, input_callback)
        print(output)
    except Exception as e:
        print(f"錯誤: {e}")


def run_repl():
    print(f"{ANSI_RESET}{highlight_ansi('📢 EmoLang 直譯器 v4.0 — 互動模式')}")
    print(highlight_ansi('📢 輸入 emoji 指令，或輸入 exit 離開'))
    print()

    interpreter = EmoLangEvaluator()
    interpreter.reset()
    interpreter.output = []
    buffer = []
    brace_depth = 0
    while True:
        prompt = "... " if brace_depth > 0 else ">>> "
        try:
            line = input(f"{ANSI_RESET}{prompt}")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip() == "exit":
            break
        if not line.strip() and brace_depth == 0:
            continue

        buffer.append(line)
        brace_depth += line.count("👇") - line.count("👆")

        if brace_depth == 0 and buffer:
            code = "\n".join(buffer)
            buffer = []
            print(highlight_ansi(code))
            try:
                from emolang.src.lexer import EmoLangLexer
                from emolang.src.parser import EmoLangParser
                lexer = EmoLangLexer(code)
                parser = EmoLangParser(lexer)
                stmts = parser.parse()
                interpreter.input_callback = input
                interpreter.execute(stmts)
                if interpreter.output:
                    print("\n".join(interpreter.output))
                    interpreter.output = []
            except Exception as e:
                print(f"錯誤: {e}")


if HAS_TKINTER:
    class EmoLangGUI(FoldingMixin, HighlightingMixin, OutlineMixin, HoverMixin,
                     RefactorMixin, EmojiMixin, SuggestionsMixin):
        def __init__(self, root):
            self.root = root
            self.root.title("EmoLang 直譯器 v4.0")
            self.root.geometry("900x700")

            self.interpreter = EmoLangEvaluator()
            self.next_line_suggestion = None
            self._suggestion_timer = None
            self._outline_timer_id = None
            self._outline_lines = []

            import tkinter.font as tkfont
            self.editor_font = tkfont.Font(family="Consolas", size=11)
            self.output_font = tkfont.Font(family="Consolas", size=11)
            try:
                self.root.tk.call("font", "configure", self.editor_font,
                                  "-family", ["Consolas", "{Segoe UI Emoji}"])
                self.root.tk.call("font", "configure", self.output_font,
                                  "-family", ["Consolas", "{Segoe UI Emoji}"])
            except tk.TclError:
                pass

            self.create_widgets()
            self.ghost = GhostText(self.code_text, font=self.editor_font)
            self._folded_regions = []
            self._emoji_key_mode = False
            self._emoji_key_map = {}
            self._load_emoji_key_map()

        def _safe_undo(self):
            try:
                view_frac = self.code_text.yview()[0]
                insert_pos = self.code_text.index(tk.INSERT)
                self.code_text.tag_remove("error_tag", "1.0", tk.END)
                self._error_msg = None
                self.code_text.edit_undo()
                self._apply_semantic_highlighting()
                self._schedule_outline_update()
                self._update_line_numbers()
                self.code_text.yview_moveto(view_frac)
                self.code_text.mark_set(tk.INSERT, insert_pos)
            except tk.TclError:
                pass
            self._debug_label.config(text="")

        def _safe_redo(self):
            try:
                view_frac = self.code_text.yview()[0]
                insert_pos = self.code_text.index(tk.INSERT)
                self.code_text.tag_remove("error_tag", "1.0", tk.END)
                self._error_msg = None
                self.code_text.edit_redo()
                self._apply_semantic_highlighting()
                self._schedule_outline_update()
                self._update_line_numbers()
                self.code_text.yview_moveto(view_frac)
                self.code_text.mark_set(tk.INSERT, insert_pos)
            except tk.TclError:
                pass
            self._debug_label.config(text="")

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

            sep1 = tk.Frame(toolbar, width=2, bg="#555555")
            sep1.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
            btn_fold = tk.Button(toolbar, text="📂 摺疊", command=self._fold_all,
                                 bg="#2c3e50", fg="white", font=("Arial", 8))
            btn_fold.pack(side=tk.LEFT, padx=2, pady=5)
            btn_unfold = tk.Button(toolbar, text="📂 展開", command=self._unfold_all,
                                   bg="#2c3e50", fg="white", font=("Arial", 8))
            btn_unfold.pack(side=tk.LEFT, padx=2, pady=5)

            sep2 = tk.Frame(toolbar, width=2, bg="#555555")
            sep2.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
            btn_undo = tk.Button(toolbar, text="↩ 復原",
                                 command=self._safe_undo,
                                 bg="#2c3e50", fg="white", font=("Arial", 8))
            btn_undo.pack(side=tk.LEFT, padx=2, pady=5)
            btn_redo = tk.Button(toolbar, text="↪ 重做",
                                 command=self._safe_redo,
                                 bg="#2c3e50", fg="white", font=("Arial", 8))
            btn_redo.pack(side=tk.LEFT, padx=2, pady=5)

            sep3 = tk.Frame(toolbar, width=2, bg="#555555")
            sep3.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
            btn_errors = tk.Button(toolbar, text="⚠ 錯誤", command=self._show_diagnostics,
                                   bg="#c0392b", fg="white", font=("Arial", 8))
            btn_errors.pack(side=tk.LEFT, padx=2, pady=5)

            self.emoji_toggle = tk.Button(toolbar, text="🔣 鍵盤", command=self.toggle_emoji,
                                           bg="#8e44ad", fg="white",
                                           font=("Segoe UI Emoji", 10), width=7)
            self.emoji_toggle.pack(side=tk.RIGHT, padx=5, pady=5)

            self.key_mode_btn = tk.Button(toolbar, text="⌨️ 模式", command=self.toggle_emoji_key_mode,
                                          bg="#2c3e50", fg="white",
                                          font=("Segoe UI Emoji", 10), width=7)
            self.key_mode_btn.pack(side=tk.RIGHT, padx=5, pady=5)
            self.emoji_key_config_btn = tk.Button(toolbar, text="⚙ 設定", command=self._configure_emoji_keys,
                                                  bg="#2c3e50", fg="white",
                                                  font=("Segoe UI Emoji", 10), width=6)
            self.emoji_key_config_btn.pack(side=tk.RIGHT, padx=2, pady=5)

            self.emoji_frame = tk.Frame(self.root, bg="#2c3e50")

            emoji_blocks = [
                ("📦 變數‧流程", ["📦", "📝", "🔢", "🎈", "🚦", "🟰", "📢", "📥", "🤔", "🤷", "🔁", "🎡", "🚧", "👇", "👆"]),
                ("🛠 函式‧資料", ["🛠", "🔙", "🏗️", "🆕", "➡️", "📍", "🎯", "📌", "📚", "📋", "📖", "🛒", "📏", "🟢", "🔴"]),
                ("➕ 運算‧比較", ["➕", "➖", "✖️", "➗", "✂️", "🤝", "📈", "📉", "🔗", "🔀", "🙅"]),
            ]
            for block_label, emojis in emoji_blocks:
                block_f = tk.Frame(self.emoji_frame, bg="#2c3e50")
                block_f.pack(fill=tk.X, padx=4, pady=1)
                lbl = tk.Label(block_f, text=block_label, bg="#2c3e50", fg="#8e8e8e",
                               font=("Consolas", 8), anchor=tk.W)
                lbl.pack(side=tk.LEFT, padx=(4, 6))
                for emoji in emojis:
                    display = emoji.replace('\ufe0f', '')
                    btn = tk.Button(block_f, text=display, font=("Segoe UI Emoji", 12),
                                  bg="#34495e", fg="white", relief=tk.RIDGE,
                                  bd=1, width=2, padx=2, pady=1,
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

            outline_tab = tk.Frame(left_frame, bg="#252526")
            outline_tab.grid(row=0, column=0, sticky=tk.EW, padx=(10, 5), pady=0)
            outline_header = tk.Label(outline_tab, text="📋 大綱", font=("Arial", 10, "bold"),
                                     bg="#2d2d2d", fg="#cccccc", pady=4)
            outline_header.pack(fill=tk.X)

            code_tab = tk.Frame(left_frame, bg="#ecf0f1")
            code_tab.grid(row=0, column=1, sticky=tk.EW, padx=(0, 10), pady=0)
            code_label = tk.Label(code_tab, text="📝 程式碼", font=("Arial", 12, "bold"), bg="#ecf0f1")
            code_label.pack(side=tk.LEFT)

            outline_frame = tk.Frame(left_frame, bg="#252526", width=170)
            outline_frame.grid(row=1, column=0, sticky="ns", padx=(10, 5), pady=5)
            outline_frame.grid_propagate(False)

            code_container = tk.Frame(left_frame, bg="#1e1e1e")
            code_container.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
            code_container.grid_columnconfigure(1, weight=1)
            code_container.grid_rowconfigure(0, weight=1)

            self.line_numbers = tk.Text(code_container, width=6, font=self.editor_font,
                                         bg="#252526", fg="#858585", relief=tk.FLAT,
                                         state='disabled', wrap=tk.NONE, padx=4, cursor="arrow",
                                         highlightthickness=0, borderwidth=0,
                                         yscrollcommand=lambda *a: None)
            self.line_numbers.grid(row=0, column=0, sticky="ns")

            self.code_text = tk.Text(code_container, font=self.editor_font,
                                     bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                                     wrap=tk.NONE, tabs=("1c",), undo=True,
                                     maxundo=-1,
                                     yscrollcommand=self._sync_line_numbers_scroll,
                                     highlightthickness=0, borderwidth=0)
            self.code_text.grid(row=0, column=1, sticky="nsew")

            self.code_scrollbar = tk.Scrollbar(code_container, command=self._on_code_scroll)
            self.code_scrollbar.grid(row=0, column=2, sticky="ns")

            self._error_label = tk.Label(left_frame, text="✔ 就緒", font=("Consolas", 9),
                                        bg="#1e1e1e", fg="#6a9955", anchor=tk.W, padx=10)
            self._error_label.grid(row=2, column=1, sticky="ew", padx=(5, 10))
            self._error_msg = None
            self._debug_label = tk.Label(left_frame, text="", font=("Consolas", 8),
                                        bg="#1e1e1e", fg="#888888", anchor=tk.W, padx=10)
            self._debug_label.grid(row=3, column=1, sticky="ew", padx=(5, 10))

            self.outline_listbox = tk.Listbox(outline_frame, bg="#1e1e1e", fg="#d4d4d4",
                                             font=("Consolas", 10), selectbackground="#264f78",
                                             relief=tk.FLAT, borderwidth=0, highlightthickness=0)
            self.outline_listbox.pack(fill=tk.BOTH, expand=True)
            self.outline_listbox.bind("<<ListboxSelect>>", self._on_outline_select)

            left_frame.grid_rowconfigure(1, weight=1)
            left_frame.grid_columnconfigure(0, weight=0)
            left_frame.grid_columnconfigure(1, weight=1)

            self._setup_tags()
            self._highlight_after_id = None
            self._hover_timer_id = None

            self.code_text.bind('<KeyRelease>', self.on_key_release)
            self.code_text.bind('<Return>', self.on_enter)
            self.code_text.bind('<Tab>', self.on_tab)
            self.code_text.bind('<Motion>', self.on_mouse_move)
            self.code_text.bind('<Leave>', self._on_mouse_leave)
            self.code_text.bind('<F2>', self._rename_symbol)
            self.code_text.bind('<Control-o>', lambda e: self.open_file() or "break")
            self.code_text.bind('<Control-n>', lambda e: self.new_file() or "break")
            self.code_text.bind('<Control-s>', lambda e: self.save_file() or "break")
            self.code_text.bind('<Control-Shift-F>', self._show_references)
            self.code_text.bind('<MouseWheel>', self._on_code_mousewheel)
            self.code_text.bind('<Button-4>', self._on_code_mousewheel)
            self.code_text.bind('<Button-5>', self._on_code_mousewheel)
            self.line_numbers.bind('<MouseWheel>', self._on_line_numbers_mousewheel)
            self.line_numbers.bind('<Button-4>', self._on_line_numbers_mousewheel)
            self.line_numbers.bind('<Button-5>', self._on_line_numbers_mousewheel)
            self.code_text.bind('<KeyPress>', self._on_code_keypress, add='+')
            self.code_text.bind('<Control-z>', lambda e: self._safe_undo() or "break")
            self.root.bind('<Control-z>', lambda e: self._safe_undo() or "break")
            self.code_text.bind('<Control-y>', lambda e: self._safe_redo() or "break")
            self.root.bind('<Control-y>', lambda e: self._safe_redo() or "break")

            self.root.after(100, self._apply_semantic_highlighting)

            right_frame = tk.Frame(self.paned, bg="#ecf0f1")
            self.paned.add(right_frame, width=450)

            output_label = tk.Label(right_frame, text="📢 輸出結果", font=("Arial", 12, "bold"), bg="#ecf0f1")
            output_label.pack(anchor=tk.W, padx=10, pady=5)

            self.output_text = scrolledtext.ScrolledText(right_frame, font=self.output_font,
                                                bg="#f8f9fa", fg="#2c3e50", state='disabled')
            self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            self.input_dialog = None
            self._hover_tooltip = None

        def _tcl_col(self, line_text, py_col_1based):
            prefix = line_text[:py_col_1based - 1] if py_col_1based > 0 else ""
            return sum(2 if ord(c) > 0xFFFF else 1 for c in prefix)

        def _tcl_len(self, s):
            return sum(2 if ord(c) > 0xFFFF else 1 for c in s)

        def _setup_tags(self):
            self.code_text.tag_configure("error_tag", background="#5a2020", underline=True)
            for name, cfg in SEMANTIC_TAG_MAP.items():
                self.code_text.tag_configure(name, foreground=cfg["fg"])
            self.code_text.tag_configure("hover_tag", underline=True, underlinefg="#569cd6")
            self.line_numbers.tag_configure("error_gutter", foreground="#f44747")
            self.code_text.tag_configure("fold_marker", foreground="#6a9955")
            self.code_text.tag_bind("fold_marker", "<Button-1>", self._on_fold_click)
            self._update_line_numbers()

        def _sync_line_numbers_scroll(self, *args):
            self.code_scrollbar.set(*args)
            if args:
                try:
                    self.line_numbers.yview_moveto(float(args[0]))
                except tk.TclError:
                    pass

        def _on_code_scroll(self, *args):
            self.code_text.yview(*args)
            self.line_numbers.yview(*args)

        def _on_code_mousewheel(self, event):
            if event.num == 4:
                self.code_text.yview_scroll(-3, "units")
                self.line_numbers.yview_scroll(-3, "units")
            elif event.num == 5:
                self.code_text.yview_scroll(3, "units")
                self.line_numbers.yview_scroll(3, "units")
            else:
                delta = -1 if event.delta > 0 else 1
                self.code_text.yview_scroll(delta * 3, "units")
                self.line_numbers.yview_scroll(delta * 3, "units")
            return "break"

        def _on_code_keypress(self, event):
            if self._emoji_key_mode and event.char and event.char in self._emoji_key_map:
                self.insert_emoji(self._emoji_key_map[event.char])
                return "break"
            self.root.after_idle(self._sync_line_numbers_after_key)

        def _sync_line_numbers_after_key(self):
            try:
                frac = self.code_text.yview()[0]
                self.line_numbers.yview_moveto(frac)
            except tk.TclError:
                pass

        def _on_line_numbers_mousewheel(self, event):
            self._on_code_mousewheel(event)

        def _update_line_numbers(self):
            self.line_numbers.config(state='normal')
            self.line_numbers.delete("1.0", tk.END)
            self.line_numbers.tag_remove("error_gutter", "1.0", tk.END)
            count = int(self.code_text.index(tk.END).split(".")[0]) - 1
            nums = "\n".join(str(i) for i in range(1, count + 1))
            self.line_numbers.insert("1.0", nums)
            for err_line, _ in getattr(self, '_all_errors', []):
                if 1 <= err_line <= count:
                    self.line_numbers.tag_add("error_gutter", f"{err_line}.0", f"{err_line}.0 lineend")
            self.line_numbers.config(state='disabled')

        def new_file(self):
            self._unfold_all()
            self.code_text.delete(1.0, tk.END)
            self.code_text.edit_reset()
            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state='disabled')
            self.root.after(100, self._apply_semantic_highlighting)
            self._schedule_outline_update()
            self._update_line_numbers()

        def open_file(self):
            filename = filedialog.askopenfilename(filetypes=[("EmoLang 檔案", "*.emo"), ("文字檔", "*.txt"), ("所有檔案", "*.*")])
            if filename:
                self._unfold_all()
                with open(filename, "r", encoding="utf-8") as f:
                    self.code_text.delete(1.0, tk.END)
                    self.code_text.insert(1.0, f.read())
                self.root.after(100, self._apply_semantic_highlighting)
                self._schedule_outline_update()
                self._update_line_numbers()

        def save_file(self):
            filename = filedialog.asksaveasfilename(defaultextension=".emo",
                                                filetypes=[("EmoLang 檔案", "*.emo"), ("文字檔", "*.txt")])
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.code_text.get(1.0, tk.END))

        def run_code(self):
            if self._folded_regions:
                self._unfold_all()
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


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "-i" or sys.argv[1] == "--interactive":
            if HAS_TKINTER:
                root = tk.Tk()
                app = EmoLangGUI(root)
                root.mainloop()
            else:
                run_repl()
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
            print()
            run_repl()


if __name__ == "__main__":
    main()
