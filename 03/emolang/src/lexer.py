from tokens import TokenType, Token


class EmoLangLexer:
    def __init__(self, src):
        self.src = src
        self.pos = 0
        self.current_token = None

        self.emoji_keywords = {
            "📦": TokenType.TOK_LET,
            "🔢": TokenType.TOK_LET,
            "🎈": TokenType.TOK_LET,
            "📝": TokenType.TOK_LET,
            "🚦": TokenType.TOK_LET,
            "🟰": TokenType.TOK_ASSIGN,
            "🤔": TokenType.TOK_IF,
            "🤷": TokenType.TOK_ELSE,
            "🔁": TokenType.TOK_WHILE,
            "👇": TokenType.TOK_LBRACE,
            "👆": TokenType.TOK_RBRACE,
            "📢": TokenType.TOK_PRINT,
            "➕": TokenType.TOK_PLUS,
            "➖": TokenType.TOK_MINUS,
            "✖️": TokenType.TOK_MUL,
            "➗": TokenType.TOK_DIV,
            "✂️": TokenType.TOK_MOD,
            "🤝": TokenType.TOK_EQ,
            "📈": TokenType.TOK_GT,
            "📉": TokenType.TOK_LT,
            "🎡": TokenType.TOK_FOR,
            "🚧": TokenType.TOK_SEP,
            "🏗️": TokenType.TOK_STRUCT,
            "🆕": TokenType.TOK_NEW,
            "➡️": TokenType.TOK_DOT,
            "📍": TokenType.TOK_REF,
            "🎯": TokenType.TOK_DEREF,
            "📚": TokenType.TOK_ARRAY,
            "📌": TokenType.TOK_INDEX,
            "📥": TokenType.TOK_INPUT,
            "🟢": TokenType.TOK_TRUE,
            "🔴": TokenType.TOK_FALSE,
            "🛠️": TokenType.TOK_FUNC,
            "🔙": TokenType.TOK_RETURN,
            "🔗": TokenType.TOK_AND,
            "🔀": TokenType.TOK_OR,
            "🙅": TokenType.TOK_NOT,
        }

    def skip_space(self):
        while self.pos < len(self.src) and self.src[self.pos].isspace():
            self.pos += 1

    def match_keyword(self):
        for kw in self.emoji_keywords:
            if self.src.startswith(kw, self.pos):
                return kw
        return None

    def advance(self):
        self.skip_space()
        if self.pos >= len(self.src):
            self.current_token = Token(TokenType.TOK_EOF, "")
            return

        if self.src[self.pos] == '(':
            self.current_token = Token(TokenType.TOK_LPAREN, "(")
            self.pos += 1
            return
        if self.src[self.pos] == ')':
            self.current_token = Token(TokenType.TOK_RPAREN, ")")
            self.pos += 1
            return
        if self.src[self.pos] == ',':
            self.current_token = Token(TokenType.TOK_COMMA, ",")
            self.pos += 1
            return

        if self.src[self.pos] == '"':
            self.pos += 1
            value = ""
            while self.pos < len(self.src) and self.src[self.pos] != '"':
                value += self.src[self.pos]
                self.pos += 1
            if self.pos < len(self.src):
                self.pos += 1
            self.current_token = Token(TokenType.TOK_STR, value)
            return

        if self.src[self.pos].isdigit():
            is_float = False
            value = ""
            while self.pos < len(self.src) and (self.src[self.pos].isdigit() or self.src[self.pos] == '.'):
                if self.src[self.pos] == '.':
                    is_float = True
                value += self.src[self.pos]
                self.pos += 1
            self.current_token = Token(TokenType.TOK_FLOAT_NUM if is_float else TokenType.TOK_NUM, value)
            return

        kw = self.match_keyword()
        if kw:
            self.current_token = Token(self.emoji_keywords[kw], kw)
            self.pos += len(kw)
            return

        value = ""
        while self.pos < len(self.src) and not self.src[self.pos].isspace():
            if self.match_keyword():
                break
            if self.src[self.pos] in '(),':
                break
            value += self.src[self.pos]
            self.pos += 1
        self.current_token = Token(TokenType.TOK_ID, value)

    def eat(self, expected_type):
        if self.current_token.type == expected_type:
            self.advance()
        else:
            raise RuntimeError(f"語法錯誤: 期待 {expected_type}，但遇到 {self.current_token.type}")