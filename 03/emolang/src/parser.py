from emolang.src.tokens import TokenType
from emolang.src.ast import ASTType, ASTNode


# Tokens that can start a statement — used by diagnostic parser for error recovery
_STATEMENT_STARTERS = {
    TokenType.TOK_LET, TokenType.TOK_PRINT, TokenType.TOK_IF,
    TokenType.TOK_ELSE, TokenType.TOK_WHILE, TokenType.TOK_FOR,
    TokenType.TOK_STRUCT, TokenType.TOK_FUNC, TokenType.TOK_RETURN,
    TokenType.TOK_LBRACE, TokenType.TOK_RBRACE,
    TokenType.TOK_ID,
    TokenType.TOK_NUM, TokenType.TOK_FLOAT_NUM, TokenType.TOK_STR,
    TokenType.TOK_TRUE, TokenType.TOK_FALSE,
    TokenType.TOK_LPAREN,
    TokenType.TOK_NOT, TokenType.TOK_INPUT, TokenType.TOK_REF,
    TokenType.TOK_DEREF, TokenType.TOK_LEN, TokenType.TOK_NEW,
}


class EmoLangParser:
    def __init__(self, lexer):
        self.lexer = lexer

    def create_node(self, ast_type):
        tok = self.lexer.current_token
        return ASTNode(ast_type, line=tok.line, col=tok.col)

    def parse(self):
        self.lexer.advance()
        statements = []
        while self.lexer.current_token.type != TokenType.TOK_EOF:
            stmt = self.parse_statement()
            statements.append(stmt)
        return statements

    def parse_expression(self):
        node = self.parse_logical_and()
        while self.lexer.current_token.type == TokenType.TOK_OR:
            new_node = self.create_node(ASTType.AST_BINOP)
            new_node.op = self.lexer.current_token.type
            new_node.left = node
            self.lexer.advance()
            new_node.right = self.parse_logical_and()
            node = new_node
        return node

    def parse_logical_and(self):
        node = self.parse_comparison()
        while self.lexer.current_token.type == TokenType.TOK_AND:
            new_node = self.create_node(ASTType.AST_BINOP)
            new_node.op = self.lexer.current_token.type
            new_node.left = node
            self.lexer.advance()
            new_node.right = self.parse_comparison()
            node = new_node
        return node

    def parse_comparison(self):
        node = self.parse_addition()
        while self.lexer.current_token.type in [TokenType.TOK_EQ, TokenType.TOK_GT, TokenType.TOK_LT]:
            new_node = self.create_node(ASTType.AST_BINOP)
            new_node.op = self.lexer.current_token.type
            new_node.left = node
            self.lexer.advance()
            new_node.right = self.parse_addition()
            node = new_node
        return node

    def parse_addition(self):
        node = self.parse_factor()
        while self.lexer.current_token.type in [TokenType.TOK_PLUS, TokenType.TOK_MINUS]:
            new_node = self.create_node(ASTType.AST_BINOP)
            new_node.op = self.lexer.current_token.type
            new_node.left = node
            self.lexer.advance()
            new_node.right = self.parse_factor()
            node = new_node
        return node

    def parse_factor(self):
        node = self.parse_prefix()
        while self.lexer.current_token.type in [TokenType.TOK_MUL, TokenType.TOK_DIV, TokenType.TOK_MOD]:
            new_node = self.create_node(ASTType.AST_BINOP)
            new_node.op = self.lexer.current_token.type
            new_node.left = node
            self.lexer.advance()
            new_node.right = self.parse_prefix()
            node = new_node
        return node

    # Parse only prefix operators (no postfix wrapping inside)
    def parse_prefix_only(self):
        if self.lexer.current_token.type == TokenType.TOK_NOT:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_NOT)
            node.left = self.parse_prefix_only()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_INPUT:
            self.lexer.advance()
            return self.create_node(ASTType.AST_INPUT)
        elif self.lexer.current_token.type == TokenType.TOK_REF:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_REF)
            node.left = self.parse_prefix_only()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_DEREF:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_DEREF)
            node.left = self.parse_prefix_only()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_LEN:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_LEN)
            node.left = self.parse_prefix_only()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_NEW:
            self.lexer.advance()
            if self.lexer.current_token.type == TokenType.TOK_LIST:
                self.lexer.advance()
                return self.create_node(ASTType.AST_NEW_LIST)
            elif self.lexer.current_token.type == TokenType.TOK_DICT:
                self.lexer.advance()
                return self.create_node(ASTType.AST_NEW_DICT)
            elif self.lexer.current_token.type == TokenType.TOK_ARRAY:
                self.lexer.advance()
                node = self.create_node(ASTType.AST_ARRAY_ALLOC)
                node.left = self.parse_primary()
                return node
            else:
                node = self.create_node(ASTType.AST_NEW)
                node.name = self.lexer.current_token.value
                self.lexer.advance()
                return node
        return self.parse_primary()

    # Prefix then postfix: handle prefix ops, then wrap with postfix (dot/index)
    def parse_prefix(self):
        node = self.parse_prefix_only()
        # Apply postfix operators (dot/index) which have higher precedence
        while self.lexer.current_token.type in [TokenType.TOK_DOT, TokenType.TOK_INDEX]:
            if self.lexer.current_token.type == TokenType.TOK_DOT:
                self.lexer.advance()
                new_node = self.create_node(ASTType.AST_DOT)
                new_node.left = node
                new_node.name = self.lexer.current_token.value
                self.lexer.advance()
                node = new_node
            elif self.lexer.current_token.type == TokenType.TOK_INDEX:
                self.lexer.advance()
                new_node = self.create_node(ASTType.AST_INDEX)
                new_node.left = node
                new_node.right = self.parse_primary()
                node = new_node
        return node

    def parse_primary(self):
        if self.lexer.current_token.type == TokenType.TOK_LPAREN:
            self.lexer.advance()
            node = self.parse_expression()
            self.lexer.eat(TokenType.TOK_RPAREN)
            return node

        node = self.create_node(ASTType.AST_NUM)
        if self.lexer.current_token.type == TokenType.TOK_NUM:
            node.value = int(self.lexer.current_token.value)
            self.lexer.advance()
        elif self.lexer.current_token.type == TokenType.TOK_FLOAT_NUM:
            node.type = ASTType.AST_FLOAT
            node.f_val = float(self.lexer.current_token.value)
            self.lexer.advance()
        elif self.lexer.current_token.type == TokenType.TOK_TRUE:
            node.type = ASTType.AST_TRUE
            self.lexer.advance()
        elif self.lexer.current_token.type == TokenType.TOK_FALSE:
            node.type = ASTType.AST_FALSE
            self.lexer.advance()
        elif self.lexer.current_token.type == TokenType.TOK_STR:
            node.type = ASTType.AST_STR
            node.name = self.lexer.current_token.value
            self.lexer.advance()
        elif self.lexer.current_token.type == TokenType.TOK_ID:
            id_name = self.lexer.current_token.value
            self.lexer.advance()

            if self.lexer.current_token.type == TokenType.TOK_LPAREN:
                self.lexer.advance()
                node.type = ASTType.AST_FUNC_CALL
                node.name = id_name
                args = []
                while self.lexer.current_token.type != TokenType.TOK_RPAREN and self.lexer.current_token.type != TokenType.TOK_EOF:
                    args.append(self.parse_expression())
                    if self.lexer.current_token.type == TokenType.TOK_COMMA:
                        self.lexer.advance()
                self.lexer.eat(TokenType.TOK_RPAREN)
                node.left = args
                return node
            else:
                node.type = ASTType.AST_VAR
                node.name = id_name
        else:
            raise RuntimeError("解析表達式出錯")
        return node

    def parse_block(self):
        self.lexer.eat(TokenType.TOK_LBRACE)
        statements = []
        while self.lexer.current_token.type != TokenType.TOK_RBRACE and self.lexer.current_token.type != TokenType.TOK_EOF:
            statements.append(self.parse_statement())
        self.lexer.eat(TokenType.TOK_RBRACE)
        return statements

    # ── Error-tolerant (diagnostic) parsing ──
    # Used by the GUI to collect all errors without cascading false positives.
    # Key idea: when a block-opening LBRACE is missing, record the error and
    # return an empty block, allowing the parser to continue with the rest.

    def diag_parse(self):
        self.diag_errors = []
        try:
            self.lexer.advance()
        except RuntimeError as e:
            self.diag_errors.append((self.lexer.line, str(e)))
            return []
        statements = []
        while self.lexer.current_token.type != TokenType.TOK_EOF:
            if self.lexer.current_token.type in _STATEMENT_STARTERS:
                try:
                    stmt = self._diag_parse_statement()
                    if stmt:
                        statements.append(stmt)
                except RuntimeError as e:
                    self.diag_errors.append((self.lexer.current_token.line, str(e)))
                    self.lexer.advance()
            else:
                self.diag_errors.append((self.lexer.current_token.line,
                    f"語法錯誤: 多餘的 {self.lexer.current_token.type}"))
                self.lexer.advance()
        return statements

    def _diag_eat(self, expected_type):
        if self.lexer.current_token.type == expected_type:
            self.lexer.advance()
        else:
            tok = self.lexer.current_token
            self.diag_errors.append((tok.line, f"語法錯誤: 期待 {expected_type}，但遇到 {tok.type}"))
            self.lexer.advance()

    def _diag_parse_block(self):
        if self.lexer.current_token.type != TokenType.TOK_LBRACE:
            tok = self.lexer.current_token
            self.diag_errors.append((tok.line, f"語法錯誤: 期待 {TokenType.TOK_LBRACE}，但遇到 {tok.type}"))
            return []
        self.lexer.advance()
        stmts = []
        while self.lexer.current_token.type != TokenType.TOK_EOF:
            if self.lexer.current_token.type == TokenType.TOK_RBRACE:
                self.lexer.advance()
                return stmts
            stmt = self._diag_parse_statement()
            if stmt:
                stmts.append(stmt)
        tok = self.lexer.current_token
        self.diag_errors.append((tok.line, f"語法錯誤: 期待 RBRACE，但遇到 EOF"))
        return stmts

    def _diag_parse_statement(self):
        if self.lexer.current_token.type == TokenType.TOK_FUNC:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_FUNC_DEF)
            node.name = self.lexer.current_token.value
            self.lexer.advance()
            self._diag_eat(TokenType.TOK_LPAREN)
            params = []
            while self.lexer.current_token.type not in (TokenType.TOK_RPAREN, TokenType.TOK_EOF):
                param = self.create_node(ASTType.AST_VAR)
                param.name = self.lexer.current_token.value
                self.lexer.advance()
                params.append(param)
                if self.lexer.current_token.type == TokenType.TOK_COMMA:
                    self.lexer.advance()
            self._diag_eat(TokenType.TOK_RPAREN)
            node.left = params
            node.body = self._diag_parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_RETURN:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_RETURN)
            node.left = self.parse_expression()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_LET:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_LET)
            node.name = self.lexer.current_token.value
            self.lexer.advance()
            if self.lexer.current_token.type == TokenType.TOK_ASSIGN:
                self.lexer.advance()
                node.left = self.parse_expression()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_PRINT:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_PRINT)
            node.left = self.parse_expression()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_IF:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_IF)
            node.left = self.parse_expression()
            node.true_branch = self._diag_parse_block()
            if self.lexer.current_token.type == TokenType.TOK_ELSE:
                self.lexer.advance()
                if self.lexer.current_token.type == TokenType.TOK_IF:
                    node.false_branch = [self._diag_parse_statement()]
                else:
                    node.false_branch = self._diag_parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_WHILE:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_WHILE)
            node.left = self.parse_expression()
            node.true_branch = self._diag_parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_FOR:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_FOR)
            node.left = self._diag_parse_statement()
            self._diag_eat(TokenType.TOK_SEP)
            node.cond = self.parse_expression()
            self._diag_eat(TokenType.TOK_SEP)
            node.step = self._diag_parse_statement()
            node.body = self._diag_parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_STRUCT:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_STRUCT_DEF)
            node.name = self.lexer.current_token.value
            self.lexer.advance()
            node.body = self._diag_parse_block()
            return node

        elif self.lexer.current_token.type in (
            TokenType.TOK_RBRACE, TokenType.TOK_LBRACE, TokenType.TOK_ELSE,
            TokenType.TOK_RPAREN, TokenType.TOK_COMMA,
            TokenType.TOK_SEP,
        ):
            tok = self.lexer.current_token
            self.diag_errors.append((tok.line, f"語法錯誤: 多餘的 {tok.type}"))
            self.lexer.advance()
            return None

        try:
            expr = self.parse_expression()
            if self.lexer.current_token.type == TokenType.TOK_ASSIGN:
                self.lexer.advance()
                node = self.create_node(ASTType.AST_ASSIGN)
                node.left = expr
                node.right = self.parse_expression()
                return node
            elif self.lexer.current_token.type == TokenType.TOK_APPEND:
                self.lexer.advance()
                node = self.create_node(ASTType.AST_APPEND)
                node.left = expr
                node.right = self.parse_expression()
                return node
            return expr
        except RuntimeError as e:
            self.diag_errors.append((self.lexer.current_token.line, str(e)))
            self.lexer.advance()
            return None

    # NOTE: GUI emolang.py takes only parser.diag_errors[0] (first error)
    # to avoid cascading. The parser may produce multiple errors per session.
    # ── End of diagnostic methods ──

    def parse_statement(self):
        if self.lexer.current_token.type == TokenType.TOK_FUNC:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_FUNC_DEF)
            node.name = self.lexer.current_token.value
            self.lexer.advance()
            self.lexer.eat(TokenType.TOK_LPAREN)
            params = []
            while self.lexer.current_token.type != TokenType.TOK_RPAREN and self.lexer.current_token.type != TokenType.TOK_EOF:
                param = self.create_node(ASTType.AST_VAR)
                param.name = self.lexer.current_token.value
                self.lexer.advance()
                params.append(param)
                if self.lexer.current_token.type == TokenType.TOK_COMMA:
                    self.lexer.advance()
            self.lexer.eat(TokenType.TOK_RPAREN)
            node.left = params
            node.body = self.parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_RETURN:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_RETURN)
            node.left = self.parse_expression()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_LET:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_LET)
            node.name = self.lexer.current_token.value
            self.lexer.advance()
            if self.lexer.current_token.type == TokenType.TOK_ASSIGN:
                self.lexer.advance()
                node.left = self.parse_expression()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_PRINT:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_PRINT)
            node.left = self.parse_expression()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_IF:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_IF)
            node.left = self.parse_expression()
            node.true_branch = self.parse_block()
            if self.lexer.current_token.type == TokenType.TOK_ELSE:
                self.lexer.advance()
                if self.lexer.current_token.type == TokenType.TOK_IF:
                    node.false_branch = [self.parse_statement()]
                else:
                    node.false_branch = self.parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_WHILE:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_WHILE)
            node.left = self.parse_expression()
            node.true_branch = self.parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_FOR:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_FOR)
            node.left = self.parse_statement()
            self.lexer.eat(TokenType.TOK_SEP)
            node.cond = self.parse_expression()
            self.lexer.eat(TokenType.TOK_SEP)
            node.step = self.parse_statement()
            node.body = self.parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_STRUCT:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_STRUCT_DEF)
            node.name = self.lexer.current_token.value
            self.lexer.advance()
            node.body = self.parse_block()
            return node

        expr = self.parse_expression()
        if self.lexer.current_token.type == TokenType.TOK_ASSIGN:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_ASSIGN)
            node.left = expr
            node.right = self.parse_expression()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_APPEND:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_APPEND)
            node.left = expr
            node.right = self.parse_expression()
            return node
        return expr