#!/usr/bin/env python3
"""EmoLang Language Server Protocol (LSP) 伺服器

透過 stdin/stdout 以 JSON-RPC 與編輯器通訊，提供：
- textDocument/semanticTokens/full (語法突顯)
- textDocument/hover (滑鼠懸停資訊)
- textDocument/documentSymbol (文件符號大綱)
- textDocument/completion (自動完成)
- textDocument/didOpen / didChange (文件同步)

也可以被 emolang.py GUI 直接 import 使用 LSP 核心功能。

Usage:
    python emolang_lsp.py            # 啟動 LSP 伺服器 (給編輯器用)

參考 QiMing LSP (https://github.com/Nickh2k6/_sp) 架構。
"""

import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emolang.src.tokens import TokenType, tokenize
from emolang.src.lexer import EmoLangLexer
from emolang.src.parser import EmoLangParser


# ── LSP 核心功能 (可被 GUI import 使用) ──

BASE_COLORS = {
    "number":   "#b5cea8",
    "string":   "#ce9178",
    "operator": "#d69d85",
    "function": "#dcdcaa",
    "variable": "#d4d4d4",
}

KEYWORD_COLORS = {
    # VS Code Dark+ C 慣例：
    #   紫 #c586c0 = 控制流程 (if, else, while, for, return, switch, case)
    #   藍 #569cd6 = 型別/宣告 (int, float, char, void, struct, const)
    #   黃 #dcdcaa = 函式呼叫/定義
    TokenType.TOK_IF: "#c586c0",
    TokenType.TOK_ELSE: "#c586c0",
    TokenType.TOK_WHILE: "#c586c0",
    TokenType.TOK_FOR: "#c586c0",
    TokenType.TOK_RETURN: "#c586c0",
    TokenType.TOK_LET: "#569cd6",
    TokenType.TOK_STRUCT: "#569cd6",
    TokenType.TOK_NEW: "#569cd6",
    TokenType.TOK_LIST: "#569cd6",
    TokenType.TOK_DICT: "#569cd6",
    TokenType.TOK_ARRAY: "#569cd6",
    TokenType.TOK_TRUE: "#569cd6",
    TokenType.TOK_FALSE: "#569cd6",
    TokenType.TOK_PRINT: "#dcdcaa",
    TokenType.TOK_INPUT: "#dcdcaa",
    TokenType.TOK_FUNC: "#dcdcaa",
    TokenType.TOK_APPEND: "#dcdcaa",
    TokenType.TOK_LEN: "#dcdcaa",
    TokenType.TOK_LBRACE: "#d4d4d4",
    TokenType.TOK_RBRACE: "#d4d4d4",
    TokenType.TOK_LPAREN: "#d4d4d4",
    TokenType.TOK_RPAREN: "#d4d4d4",
    TokenType.TOK_COMMA: "#d4d4d4",
    TokenType.TOK_SEP: "#d4d4d4",
}

TAG_COLORS = dict(BASE_COLORS)
for _tok_type, _color in KEYWORD_COLORS.items():
    TAG_COLORS[f"tok_{_tok_type}"] = _color

ANSI_COLORS = {
    "keyword":  "\033[94m",
    "variable": "\033[0m",
    "function": "\033[93m",
    "number":   "\033[92m",
    "string":   "\033[91m",
    "operator": "\033[96m",
}
ANSI_RESET = "\033[0m"

_KEYWORD_SET = {
    TokenType.TOK_LET, TokenType.TOK_IF, TokenType.TOK_ELSE,
    TokenType.TOK_WHILE, TokenType.TOK_FOR, TokenType.TOK_PRINT,
    TokenType.TOK_INPUT, TokenType.TOK_FUNC, TokenType.TOK_RETURN,
    TokenType.TOK_STRUCT, TokenType.TOK_NEW, TokenType.TOK_TRUE,
    TokenType.TOK_FALSE, TokenType.TOK_LIST, TokenType.TOK_DICT,
    TokenType.TOK_ARRAY, TokenType.TOK_APPEND, TokenType.TOK_LEN,
    TokenType.TOK_LBRACE, TokenType.TOK_RBRACE,
    TokenType.TOK_LPAREN, TokenType.TOK_RPAREN, TokenType.TOK_COMMA,
    TokenType.TOK_SEP,
}

_OPERATOR_SET = {
    TokenType.TOK_PLUS, TokenType.TOK_MINUS, TokenType.TOK_MUL,
    TokenType.TOK_DIV, TokenType.TOK_MOD, TokenType.TOK_EQ,
    TokenType.TOK_GT, TokenType.TOK_LT, TokenType.TOK_AND,
    TokenType.TOK_OR, TokenType.TOK_NOT, TokenType.TOK_DOT,
    TokenType.TOK_INDEX, TokenType.TOK_REF, TokenType.TOK_DEREF,
    TokenType.TOK_ASSIGN,
}

_NUMBER_SET = {TokenType.TOK_NUM, TokenType.TOK_FLOAT_NUM}


def get_tokens(code):
    tokens = []
    lexer = EmoLangLexer(code)
    while True:
        try:
            lexer.advance()
        except RuntimeError:
            if lexer.pos < len(lexer.src):
                ch = lexer.src[lexer.pos]
                lexer.pos += 1
                if ch == '\n':
                    lexer.line += 1
                    lexer.col = 1
                else:
                    lexer.col += 1
                continue
            break
        if lexer.current_token is None or lexer.current_token.type == TokenType.TOK_EOF:
            break
        tokens.append(lexer.current_token)
    return tokens


def get_semantic_tag(tok, next_type=None):
    if tok.type in KEYWORD_COLORS:
        return f"tok_{tok.type}"
    if tok.type in _NUMBER_SET:
        return "number"
    if tok.type == TokenType.TOK_STR:
        return "string"
    if tok.type in _OPERATOR_SET:
        return "operator"
    if tok.type == TokenType.TOK_ID:
        return "function" if next_type == TokenType.TOK_LPAREN else "variable"
    return "variable"


_HOVER_TYPE_NAMES = {
    TokenType.TOK_LET: "宣告 (LET)", TokenType.TOK_ASSIGN: "賦值 (ASSIGN)",
    TokenType.TOK_IF: "條件判斷 (IF)", TokenType.TOK_ELSE: "否則分支 (ELSE)",
    TokenType.TOK_WHILE: "條件迴圈 (WHILE)", TokenType.TOK_FOR: "計數迴圈 (FOR)",
    TokenType.TOK_PRINT: "輸出 (PRINT)", TokenType.TOK_INPUT: "輸入 (INPUT)",
    TokenType.TOK_PLUS: "加法", TokenType.TOK_MINUS: "減法",
    TokenType.TOK_MUL: "乘法", TokenType.TOK_DIV: "除法", TokenType.TOK_MOD: "取餘數",
    TokenType.TOK_EQ: "相等比較", TokenType.TOK_GT: "大於", TokenType.TOK_LT: "小於",
    TokenType.TOK_AND: "邏輯 AND", TokenType.TOK_OR: "邏輯 OR", TokenType.TOK_NOT: "邏輯 NOT",
    TokenType.TOK_STRUCT: "結構體定義", TokenType.TOK_NEW: "建立實例",
    TokenType.TOK_DOT: "成員存取", TokenType.TOK_REF: "取址",
    TokenType.TOK_DEREF: "解參考", TokenType.TOK_ARRAY: "配置陣列",
    TokenType.TOK_INDEX: "索引存取", TokenType.TOK_FUNC: "函數定義",
    TokenType.TOK_RETURN: "回傳", TokenType.TOK_TRUE: "真值",
    TokenType.TOK_FALSE: "假值", TokenType.TOK_LIST: "列表",
    TokenType.TOK_DICT: "字典", TokenType.TOK_APPEND: "追加元素",
    TokenType.TOK_LEN: "計算長度", TokenType.TOK_LBRACE: "區塊開始",
    TokenType.TOK_RBRACE: "區塊結束", TokenType.TOK_SEP: "分隔符",
    TokenType.TOK_LPAREN: "左括號", TokenType.TOK_RPAREN: "右括號",
    TokenType.TOK_COMMA: "逗號",
}


def hover_content(tok):
    if tok.type == TokenType.TOK_ID:
        return f"識別字：`{tok.value}`"
    if tok.type in (TokenType.TOK_NUM, TokenType.TOK_FLOAT_NUM):
        return f"數值常數：`{tok.value}`"
    if tok.type == TokenType.TOK_STR:
        return f"字串常數：`\"{tok.value}\"`"
    desc = _HOVER_TYPE_NAMES.get(tok.type, tok.type)
    return f"{desc}  `{tok.value}`"


def highlight_ansi(code):
    tokens = tokenize(code)
    result = []
    prev_end = 0
    for tok in tokens:
        if tok.type == TokenType.TOK_EOF:
            continue
        tag = get_semantic_tag(tok)
        broad_tag = "keyword" if tag.startswith("tok_") else tag
        color = ANSI_COLORS.get(broad_tag, "")
        start_byte = len(code[:prev_end].encode('utf-8'))
        tok_start = code.find(tok.value, prev_end) if tok.value else -1
        if tok_start < 0:
            result.append(code[prev_end:])
            break
        result.append(code[prev_end:tok_start])
        result.append(f"{color}{tok.value}{ANSI_RESET}")
        prev_end = tok_start + len(tok.value)
    result.append(code[prev_end:])
    return "".join(result)


def encode_semantic_tokens(tokens):
    result = []
    prev_line = 0
    prev_col = 0
    for i, tok in enumerate(tokens):
        if tok.type == TokenType.TOK_EOF:
            continue
        next_type = tokens[i + 1].type if i + 1 < len(tokens) and tokens[i + 1].type != TokenType.TOK_EOF else None
        tag = get_semantic_tag(tok, next_type)
        broad_tag = "keyword" if tag.startswith("tok_") else tag
        type_idx = ["keyword", "variable", "function", "number", "string", "operator"].index(broad_tag)

        delta_line = tok.line - 1 - prev_line
        delta_col = tok.col - 1 - prev_col if delta_line == 0 else tok.col - 1
        result += [delta_line, delta_col, tok.char_length, type_idx, 0]
        prev_line = tok.line - 1
        prev_col = tok.col - 1 + tok.char_length
    return result


# ── LSP 文件管理 ──

class Document:
    def __init__(self, uri, content):
        self.uri = uri
        self.content = content
        self.dirty = True
        self.tokens = []
        self.ast_nodes = []
        self.diagnostics = []
        self.def_map = {}

    def update(self, content):
        self.content = content
        self.dirty = True

    def _make_diag(self, msg, tok):
        return {
            "range": {
                "start": {"line": tok.line - 1, "character": tok.col - 1},
                "end": {"line": tok.line - 1, "character": tok.col - 1 + max(tok.char_length, 1)}
            },
            "severity": 1,
            "message": str(msg),
            "source": "EmoLang"
        }

    def ensure_parsed(self):
        if not self.dirty:
            return
        self.tokens = tokenize(self.content)
        self.diagnostics = []
        self.def_map = {}
        try:
            lexer = EmoLangLexer(self.content)
            parser = EmoLangParser(lexer)
            self.ast_nodes = parser.parse()
            self._build_def_map()
        except RuntimeError as e:
            self.ast_nodes = []
            tok = getattr(lexer, 'current_token', None)
            if tok and tok.type != TokenType.TOK_EOF:
                self.diagnostics.append(self._make_diag(e, tok))
            else:
                self.diagnostics.append({
                    "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
                    "severity": 1, "message": str(e), "source": "EmoLang"
                })
        except Exception as e:
            self.ast_nodes = []
            self.diagnostics.append({
                "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
                "severity": 1, "message": str(e), "source": "EmoLang"
            })
        self.dirty = False

    def _build_def_map(self):
        name_tokens = {}
        for tok in self.tokens:
            if tok.type == TokenType.TOK_ID:
                name_tokens.setdefault(tok.value, []).append(tok)

        for stmt in self.ast_nodes:
            if stmt.type in ("LET", "FUNC_DEF"):
                candidates = name_tokens.get(stmt.name, [])
                for t in candidates:
                    if t.line == stmt.line and t.col >= stmt.col:
                        self.def_map[stmt.name] = {
                            "uri": self.uri,
                            "range": {
                                "start": {"line": t.line - 1, "character": t.col - 1},
                                "end": {"line": t.line - 1, "character": t.col - 1 + t.char_length}
                            }
                        }
                        break


# ── LSP 伺服器 (JSON-RPC over stdin/stdout) ──

KEYWORD_LIST = [
    "📦", "🔢", "🎈", "📝", "🚦",
    "🤔", "🤷", "🔁", "🎡", "📢", "📥",
    "🛠️", "🔙", "🏗️", "🆕",
    "🟢", "🔴",
    "📋", "📖", "📚", "🛒", "📏",
    "📍", "🎯", "📌", "➡️",
]


class EmoLangLSPServer:
    def __init__(self):
        self.documents = {}
        self.request_id = 0
        self._stdin = sys.stdin.buffer
        self._stdout = sys.stdout.buffer

    def run(self):
        while True:
            msg = self._read_message()
            if msg is None:
                break
            self._handle_message(msg)

    def _read_message(self):
        content_length = 0
        while True:
            line = self._stdin.readline()
            if not line:
                return None
            line = line.decode("utf-8").strip()
            if not line:
                break
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
        if content_length == 0:
            return None
        body_bytes = self._stdin.read(content_length)
        return json.loads(body_bytes.decode("utf-8"))

    def _send_message(self, message):
        body_bytes = json.dumps(message, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n"
        self._stdout.write(header.encode("utf-8"))
        self._stdout.write(body_bytes)
        self._stdout.flush()

    def _send_result(self, msg_id, result):
        self._send_message({"jsonrpc": "2.0", "id": msg_id, "result": result})

    def _handle_message(self, msg):
        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        handlers = {
            "initialize": lambda: self._send_result(msg_id, {
                "capabilities": {
                    "textDocumentSync": {"openClose": True, "change": 2, "save": {"includeText": True}},
                    "semanticTokensProvider": {"full": True, "legend": {
                        "tokenTypes": ["keyword","variable","function","number","string","operator","comment","type"],
                        "tokenModifiers": []
                    }},
                    "hoverProvider": True,
                    "documentSymbolProvider": True,
                    "completionProvider": {},
                    "definitionProvider": True,
                    "foldingRangeProvider": True,
                    "referencesProvider": True,
                    "renameProvider": {"prepareProvider": True}
                }
            }),
            "shutdown": lambda: self._send_result(msg_id, None),
            "exit": lambda: sys.exit(0),
            "textDocument/didOpen": lambda: self._handle_doc_open(
                params["textDocument"]["uri"], params["textDocument"]["text"]),
            "textDocument/didChange": lambda: self._handle_doc_change(
                params["textDocument"]["uri"], params["contentChanges"][0]["text"]),
            "textDocument/didSave": lambda: self._send_diagnostics(params["textDocument"]["uri"]),
            "textDocument/didClose": lambda: self._handle_doc_close(params["textDocument"]["uri"]),
            "textDocument/semanticTokens/full": lambda: self._send_result(
                msg_id, {"data": self._semantic_tokens(params["textDocument"]["uri"])}),
            "textDocument/hover": lambda: self._send_result(
                msg_id, self._hover(params)),
            "textDocument/documentSymbol": lambda: self._send_result(
                msg_id, self._document_symbol(params["textDocument"]["uri"])),
            "textDocument/completion": lambda: self._send_result(
                msg_id, self._completion()),
            "textDocument/definition": lambda: self._send_result(
                msg_id, self._go_to_definition(params)),
            "textDocument/foldingRange": lambda: self._send_result(
                msg_id, self._folding_range(params["textDocument"]["uri"])),
            "textDocument/references": lambda: self._send_result(
                msg_id, self._references(params)),
            "textDocument/prepareRename": lambda: self._send_result(
                msg_id, self._prepare_rename(params)),
            "textDocument/rename": lambda: self._send_result(
                msg_id, self._rename(params)),
        }
        handler = handlers.get(method)
        if handler:
            handler()
        elif msg_id is not None:
            self._send_result(msg_id, None)

    def _handle_doc_open(self, uri, text):
        self.documents[uri] = Document(uri, text)
        self._send_diagnostics(uri)

    def _handle_doc_change(self, uri, text):
        if uri in self.documents:
            self.documents[uri].update(text)
            self._send_diagnostics(uri)

    def _handle_doc_close(self, uri):
        self.documents.pop(uri, None)
        self._send_message({
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": []}
        })

    def _send_diagnostics(self, uri):
        doc = self.documents.get(uri)
        if not doc:
            return
        doc.ensure_parsed()
        self._send_message({
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": doc.diagnostics}
        })

    def _semantic_tokens(self, uri):
        doc = self.documents.get(uri)
        if not doc:
            return []
        doc.ensure_parsed()
        return encode_semantic_tokens(doc.tokens)

    def _find_ast_node_at(self, stmts, line, col):
        for stmt in stmts:
            sl, sc = stmt.line - 1, stmt.col - 1
            for child in [stmt.left, stmt.right, stmt.cond, stmt.step]:
                if child and hasattr(child, 'line'):
                    cl, cc = child.line - 1, child.col - 1
                    if cl == line and cc == col:
                        return child
            if sl == line and sc == col:
                return stmt
        return None

    def _hover(self, params):
        uri = params["textDocument"]["uri"]
        pos = params["position"]
        line, col = pos["line"], pos["character"]
        doc = self.documents.get(uri)
        if not doc:
            return None
        doc.ensure_parsed()
        node = self._find_ast_node_at(doc.ast_nodes, line, col)
        if node:
            if node.type in ("FUNC_DEF", "FUNC_CALL"):
                kind = "函式定義" if node.type == "FUNC_DEF" else "函式呼叫"
                return {"contents": {"kind": "markdown",
                    "value": f"**{kind}**\n\n名稱：`{node.name}`"}}
            if node.type == "LET":
                return {"contents": {"kind": "markdown",
                    "value": f"**變數宣告**\n\n名稱：`{node.name}`"}}
        for tok in doc.tokens:
            if tok.type == TokenType.TOK_EOF:
                continue
            tl, ts, te = tok.line - 1, tok.col - 1, tok.col - 1 + tok.char_length
            if tl == line and ts <= col < te:
                return {"contents": {"kind": "markdown", "value": hover_content(tok)}}
        return None

    def _go_to_definition(self, params):
        uri = params["textDocument"]["uri"]
        pos = params["position"]
        line, col = pos["line"], pos["character"]
        doc = self.documents.get(uri)
        if not doc:
            return None
        doc.ensure_parsed()
        for tok in doc.tokens:
            if tok.type == TokenType.TOK_EOF:
                continue
            tl, ts, te = tok.line - 1, tok.col - 1, tok.col - 1 + tok.char_length
            if tl == line and ts <= col < te:
                if tok.type == TokenType.TOK_ID and tok.value in doc.def_map:
                    return doc.def_map[tok.value]
                break
        return None

    def _document_symbol(self, uri):
        doc = self.documents.get(uri)
        if not doc:
            return []
        doc.ensure_parsed()
        symbols = []
        for i, stmt in enumerate(doc.ast_nodes):
            if stmt.type in ("FUNC_DEF", "LET"):
                kind = 12 if stmt.type == "FUNC_DEF" else 13
                start_line = stmt.line - 1
                start_col = stmt.col - 1
                if i + 1 < len(doc.ast_nodes):
                    nxt = doc.ast_nodes[i + 1]
                    end_line = nxt.line - 1
                    end_col = nxt.col - 1
                else:
                    content_lines = doc.content.split("\n")
                    end_line = len(content_lines) - 1
                    end_col = len(content_lines[-1]) if content_lines else 0
                rng = {"start": {"line": start_line, "character": start_col},
                       "end": {"line": end_line, "character": end_col}}
                symbols.append({"name": stmt.name, "kind": kind,
                    "range": rng, "selectionRange": rng})
        return symbols

    def _completion(self):
        items = [{"label": kw, "kind": 14, "detail": "EmoLang 關鍵字"} for kw in KEYWORD_LIST]
        items.append({"label": "🟰", "kind": 14, "detail": "EmoLang 關鍵字 - 賦值"})
        return items

    def _folding_range(self, uri):
        doc = self.documents.get(uri)
        if not doc:
            return []
        doc.ensure_parsed()
        brace_stack = []
        ranges = []
        for tok in doc.tokens:
            if tok.type == TokenType.TOK_LBRACE:
                brace_stack.append(tok.line - 1)
            elif tok.type == TokenType.TOK_RBRACE:
                if brace_stack:
                    start_line = brace_stack.pop()
                    end_line = tok.line - 1
                    if end_line > start_line:
                        ranges.append({
                            "startLine": start_line,
                            "endLine": end_line,
                        })
        return ranges

    def _find_token_at(self, uri, line, col):
        doc = self.documents.get(uri)
        if not doc:
            return None
        doc.ensure_parsed()
        for tok in doc.tokens:
            if tok.type == TokenType.TOK_EOF:
                continue
            tl, ts, te = tok.line - 1, tok.col - 1, tok.col - 1 + tok.char_length
            if tl == line and ts <= col < te:
                return tok
        return None

    def _references(self, params):
        uri = params["textDocument"]["uri"]
        pos = params["position"]
        line, col = pos["line"], pos["character"]
        tok = self._find_token_at(uri, line, col)
        if not tok or tok.type != TokenType.TOK_ID:
            return []
        locations = []
        doc = self.documents.get(uri)
        for t in doc.tokens:
            if t.type == TokenType.TOK_ID and t.value == tok.value:
                locations.append({
                    "uri": uri,
                    "range": {
                        "start": {"line": t.line - 1, "character": t.col - 1},
                        "end": {"line": t.line - 1, "character": t.col - 1 + t.char_length}
                    }
                })
        include_decl = params.get("context", {}).get("includeDeclaration", True)
        if not include_decl:
            def_tok = self._find_def_token(uri, tok.value)
            if def_tok:
                locations = [loc for loc in locations
                             if not (loc["range"]["start"]["line"] == def_tok.line - 1
                                     and loc["range"]["start"]["character"] == def_tok.col - 1)]
        return locations

    def _find_def_token(self, uri, name):
        doc = self.documents.get(uri)
        if not doc:
            return None
        doc.ensure_parsed()
        def_entry = doc.def_map.get(name)
        if not def_entry:
            return None
        for t in doc.tokens:
            if t.type == TokenType.TOK_ID and t.value == name:
                r = def_entry["range"]
                if t.line - 1 == r["start"]["line"] and t.col - 1 == r["start"]["character"]:
                    return t
        return None

    def _prepare_rename(self, params):
        uri = params["textDocument"]["uri"]
        pos = params["position"]
        line, col = pos["line"], pos["character"]
        tok = self._find_token_at(uri, line, col)
        if not tok or tok.type != TokenType.TOK_ID:
            return None
        return {
            "range": {
                "start": {"line": tok.line - 1, "character": tok.col - 1},
                "end": {"line": tok.line - 1, "character": tok.col - 1 + tok.char_length}
            },
            "placeholder": tok.value
        }

    def _rename(self, params):
        uri = params["textDocument"]["uri"]
        pos = params["position"]
        new_name = params.get("newName", "")
        if not new_name:
            return None
        line, col = pos["line"], pos["character"]
        tok = self._find_token_at(uri, line, col)
        if not tok or tok.type != TokenType.TOK_ID:
            return None
        edits = []
        doc = self.documents.get(uri)
        for t in doc.tokens:
            if t.type == TokenType.TOK_ID and t.value == tok.value:
                edits.append({
                    "range": {
                        "start": {"line": t.line - 1, "character": t.col - 1},
                        "end": {"line": t.line - 1, "character": t.col - 1 + t.char_length}
                    },
                    "newText": new_name
                })
        return {"changes": {uri: edits}}


def main():
    try:
        EmoLangLSPServer().run()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
