#!/usr/bin/env python3
import sys
import os
import json

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
    from emolang_lsp import get_tokens, get_semantic_tag, hover_content, TAG_COLORS
 
    SEMANTIC_TAG_MAP = {name: {"fg": color} for name, color in TAG_COLORS.items()}


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
    print(f"{ANSI_RESET}{highlight_ansi('# EmoLang 直譯器 v4.0 — 互動模式')}")
    print(highlight_ansi('# 輸入 emoji 指令，或輸入 exit 離開'))
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
    "🛠": "FUNC 定義函數",
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

EMOJI_KEY_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "emoji_keys.json")

DEFAULT_EMOJI_KEY_MAP = {
    'a': '📦', 'b': '📢', 'c': '🤔', 'd': '🔁', 'e': '📝',
    'f': '🛠', 'g': '🏗️', 'h': '👇', 'i': '📥', 'j': '👆',
    'k': '🔙', 'l': '📖', 'm': '➕', 'n': '🆕', 'o': '🔀',
    'p': '✖️', 'q': '🤷', 'r': '➡️', 's': '🙅', 't': '🟰',
    'u': '🎡', 'v': '🎯', 'w': '📈', 'x': '➖', 'y': '🤝',
    'z': '📉',
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

        def _apply_semantic_highlighting(self):
            code = self.code_text.get("1.0", tk.END)
            for name in SEMANTIC_TAG_MAP:
                self.code_text.tag_remove(name, "1.0", tk.END)
            self.code_text.tag_remove("hover_tag", "1.0", tk.END)
            self.code_text.tag_remove("error_tag", "1.0", tk.END)

            try:
                lines = code.split("\n")

                # Diagnostics — single pass with error-tolerant parser
                self._all_errors = []
                lexer = EmoLangLexer(code)
                parser = EmoLangParser(lexer)
                parser.diag_parse()
                seen_lines = set()
                for rel_line, msg in parser.diag_errors:
                    if rel_line > 0 and rel_line not in seen_lines and len(self._all_errors) < 100:
                        seen_lines.add(rel_line)
                        self._all_errors.append((rel_line, msg))

                # Error lines shown via red line numbers in gutter + error label below
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

        def _get_folding_ranges(self):
            code = self.code_text.get("1.0", tk.END)
            tokens = get_tokens(code)
            brace_stack = []
            ranges = []
            for tok in tokens:
                if tok.type == TokenType.TOK_LBRACE:
                    brace_stack.append(tok.line)
                elif tok.type == TokenType.TOK_RBRACE:
                    if brace_stack:
                        start = brace_stack.pop()
                        end = tok.line
                        if not brace_stack and end > start:
                            ranges.append((start, end))
            return ranges

        def _fold_all(self, event=None):
            if self._folded_regions:
                return
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
            self._folded_regions = folded
            if folded:
                self._debug_label.config(text=f"📂 已摺疊 {len(folded)} 個區塊，按「展開」或點擊標記還原")
            self._update_line_numbers()

        def _unfold_all(self, event=None):
            for text, marker in self._folded_regions:
                pos = self.code_text.search(marker, tk.END, backwards=True)
                if pos:
                    line = int(pos.split(".")[0])
                    self.code_text.delete(f"{line}.0", f"{line+1}.0")
                    self.code_text.insert(f"{line}.0", text)
            self._folded_regions = []
            self.code_text.tag_remove("fold_marker", "1.0", tk.END)
            self._apply_semantic_highlighting()
            self._debug_label.config(text="📂 已展開全部區塊")
            self._update_line_numbers()

        def _unfold_marker_at_line(self, line):
            for i, (text, marker) in enumerate(self._folded_regions):
                pos = self.code_text.search(marker, f"{line}.0", f"{line+1}.0")
                if pos:
                    self.code_text.delete(f"{line}.0", f"{line+1}.0")
                    self.code_text.insert(f"{line}.0", text)
                    self._folded_regions.pop(i)
                    self._apply_semantic_highlighting()
                    # Re-apply fold_marker tag to remaining regions
                    self.code_text.tag_remove("fold_marker", "1.0", tk.END)
                    for _, m in self._folded_regions:
                        p = self.code_text.search(m, tk.END, backwards=True)
                        if p:
                            pl = int(p.split(".")[0])
                            self.code_text.tag_add("fold_marker", f"{pl}.0", f"{pl+1}.0")
                    self._update_line_numbers()
                    return True
            return False

        def _on_fold_click(self, event):
            index = self.code_text.index(f"@{event.x},{event.y}")
            if index:
                line = int(index.split(".")[0])
                if self._unfold_marker_at_line(line):
                    self._debug_label.config(text=f"📂 已展開 line {line}")
            return "break"

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
                # Build the new code string in Python, then replace atomically
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
