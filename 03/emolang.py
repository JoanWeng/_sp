#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    import tkinter as tk
    from tkinter import scrolledtext, filedialog
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

            self.code_text = scrolledtext.ScrolledText(left_frame, font=self.editor_font,
                                                bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                                                wrap=tk.NONE, tabs=("1c",))
            self.code_text.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)

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
            self.code_text.bind('<F12>', self._go_to_definition)
            self.root.bind('<Control-g>', lambda e: self._go_to_definition())
            self.code_text.bind('<Control-g>', lambda e: self._go_to_definition())

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
            for name, cfg in SEMANTIC_TAG_MAP.items():
                self.code_text.tag_configure(name, foreground=cfg["fg"])
            self.code_text.tag_configure("hover_tag", underline=True, underlinefg="#569cd6")
            self.code_text.tag_configure("error_tag", foreground="#f44747", background="#3a1a1a", underline=True)

        def _apply_semantic_highlighting(self):
            code = self.code_text.get("1.0", tk.END)
            for name in SEMANTIC_TAG_MAP:
                self.code_text.tag_remove(name, "1.0", tk.END)
            self.code_text.tag_remove("hover_tag", "1.0", tk.END)
            self.code_text.tag_remove("error_tag", "1.0", tk.END)

            try:
                lines = code.split("\n")
                tokens = get_tokens(code)

                # Diagnostics — capture syntax errors
                self._error_msg = None
                try:
                    lexer = EmoLangLexer(code)
                    parser = EmoLangParser(lexer)
                    parser.parse()
                except RuntimeError as e:
                    tok = getattr(lexer, 'current_token', None)
                    if tok and tok.type == TokenType.TOK_EOF:
                        for t in reversed(tokens):
                            if t.type != TokenType.TOK_EOF:
                                tok = t
                                break
                    if tok and tok.type != TokenType.TOK_EOF and tok.line > 0 and tok.line <= len(lines):
                        line_text = lines[tok.line - 1]
                        if tok.col > 0 and tok.col <= len(line_text):
                            tc = self._tcl_col(line_text, tok.col)
                            token_src = line_text[tok.col - 1 : tok.col - 1 + max(tok.char_length, 1)]
                            if token_src:
                                tcl_end = tc + sum(2 if ord(c) > 0xFFFF else 1 for c in token_src)
                                try:
                                    self.code_text.tag_add("error_tag", f"{tok.line}.{tc}", f"{tok.line}.{tcl_end}")
                                except tk.TclError:
                                    pass
                    self._error_msg = str(e)
                except Exception as e:
                    self._error_msg = str(e)
                self._update_error_label()

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
                try:
                    self.code_text.tag_raise("error_tag")
                except tk.TclError:
                    pass
            except Exception as e:
                msg = f"[HL error] {e}"
                print(msg, file=sys.stderr)
                self._debug_label.config(text=msg)

        def _update_error_label(self):
            if self._error_msg:
                self._error_label.config(text=f"⚠ {self._error_msg}", fg="#f44747")
            else:
                self._error_label.config(text="✔ 無語法錯誤", fg="#6a9955")

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
                nodes = parser.parse()
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

        def _get_def_map(self):
            code = self.code_text.get("1.0", tk.END)
            def_map = {}
            try:
                lexer = EmoLangLexer(code)
                parser = EmoLangParser(lexer)
                nodes = parser.parse()
                tokens = get_tokens(code)
                name_tokens = {}
                for t in tokens:
                    if t.type == TokenType.TOK_ID:
                        name_tokens.setdefault(t.value, []).append(t)
                for n in nodes:
                    if n.type in ("LET", "FUNC_DEF"):
                        for t in name_tokens.get(n.name, []):
                            if t.line == n.line and t.col >= n.col:
                                def_map[n.name] = t
                                break
            except RuntimeError:
                pass
            except Exception as e:
                print(f"[_get_def_map error] {e}", file=sys.stderr)
            return def_map

        def _go_to_definition(self, event=None):
            try:
                cursor = self.code_text.index(tk.INSERT)
                line = int(cursor.split(".")[0])
                col = int(cursor.split(".")[1])
                tok = self._find_token_at(line, col)
                if not tok or tok.type != TokenType.TOK_ID:
                    self._debug_label.config(text=f"F12: no ID at ({line},{col})")
                    return None
                def_map = self._get_def_map()
                def_tok = def_map.get(tok.value)
                if not def_tok:
                    self._debug_label.config(text=f"F12: '{tok.value}' not in def_map ({len(def_map)} defs)")
                    return None
                lines = self.code_text.get("1.0", tk.END).split("\n")
                line_text = lines[def_tok.line - 1] if def_tok.line - 1 < len(lines) else ""
                tc = self._tcl_col(line_text, def_tok.col)
                self.code_text.see(f"{def_tok.line}.{tc}")
                self.code_text.mark_set(tk.INSERT, f"{def_tok.line}.{tc}")
                self.code_text.focus_set()
                self._debug_label.config(text=f"F12: → line {def_tok.line}")
                return "break"
            except Exception as e:
                self._debug_label.config(text=f"F12 error: {e}")
                return None

        def new_file(self):
            self.code_text.delete(1.0, tk.END)
            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state='disabled')
            self.root.after(100, self._apply_semantic_highlighting)
            self._schedule_outline_update()

        def open_file(self):
            filename = filedialog.askopenfilename(filetypes=[("EmoLang 檔案", "*.emo"), ("文字檔", "*.txt"), ("所有檔案", "*.*")])
            if filename:
                with open(filename, "r", encoding="utf-8") as f:
                    self.code_text.delete(1.0, tk.END)
                    self.code_text.insert(1.0, f.read())
                self.root.after(100, self._apply_semantic_highlighting)
                self._schedule_outline_update()

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
            self._apply_semantic_highlighting()
            self._schedule_outline_update()
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
