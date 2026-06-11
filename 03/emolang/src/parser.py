from emolang.src.tokens import TokenType
from emolang.src.ast import ASTType, ASTNode


# Expression node types that, as standalone statements, likely indicate a missing 📢
_BARE_EXPR_TYPES = {
    ASTType.AST_NUM, ASTType.AST_FLOAT,
    ASTType.AST_TRUE, ASTType.AST_FALSE,
    ASTType.AST_STR, ASTType.AST_BINOP,
}

# Tokens that can start an expression (subset of _STATEMENT_STARTERS minus keywords/blocks)
_EXPR_STARTERS = {
    TokenType.TOK_ID,
    TokenType.TOK_NUM, TokenType.TOK_FLOAT_NUM, TokenType.TOK_STR,
    TokenType.TOK_TRUE, TokenType.TOK_FALSE,
    TokenType.TOK_LPAREN,
    TokenType.TOK_NOT, TokenType.TOK_INPUT, TokenType.TOK_REF,
    TokenType.TOK_DEREF, TokenType.TOK_LEN, TokenType.TOK_NEW,
}

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

    @staticmethod
    def _is_name_type(tok):
        return tok.type in (
            TokenType.TOK_ID, TokenType.TOK_NUM, TokenType.TOK_FLOAT_NUM,
            TokenType.TOK_STR, TokenType.TOK_TRUE, TokenType.TOK_FALSE,
        )

    def _check_name(self, tok):
        """Validate that a name token doesn't start with a digit."""
        if tok.value and tok.value[0].isdigit():
            raise RuntimeError(f"第 {tok.line} 行: 識別字不能以數字開頭")
        if not self._is_name_type(tok):
            raise RuntimeError(f"第 {tok.line} 行: 語法錯誤: 缺少名稱")

    def _diag_check_name(self, tok):
        """Validate name in diagnostic mode — records error, returns False on failure."""
        if not self._is_name_type(tok):
            self.diag_errors.append((tok.line, f"語法錯誤: 缺少名稱"))
            return False
        if tok.value and tok.value[0].isdigit():
            self.diag_errors.append((tok.line, f"第 {tok.line} 行: 識別字不能以數字開頭"))
            return False
        return True

    def _diag_skip_to_statement(self):
        """Skip past the invalid name and any remaining tokens of the broken construct."""
        self.lexer.advance()  # skip the invalid name token
        while self.lexer.current_token.type != TokenType.TOK_EOF:
            t = self.lexer.current_token.type
            if t in _STATEMENT_STARTERS and \
               t not in (TokenType.TOK_LBRACE, TokenType.TOK_RBRACE, TokenType.TOK_LPAREN):
                break
            self.lexer.advance()

    def _diag_check_undeclared_vars(self, node):
        """Recursively check an AST node for undeclared variable references."""
        if node is None:
            return
        if node.type == ASTType.AST_VAR:
            if node.name not in self._declared_vars:
                self.diag_errors.append((node.line, f"語法錯誤: 未宣告變數「{node.name}」"))
        for child in [node.left, node.right, node.cond, node.step]:
            if child is not None:
                if isinstance(child, list):
                    for c in child:
                        self._diag_check_undeclared_vars(c)
                else:
                    self._diag_check_undeclared_vars(child)

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
        self._declared_vars = set()
        try:
            self.lexer.advance()
        except RuntimeError as e:
            self.diag_errors.append((self.lexer.line, str(e)))
            return []
        statements = []
        _prev_tok_type = None
        _prev_tok_line = -1
        _prev_tok_col = -1
        while self.lexer.current_token.type != TokenType.TOK_EOF:
            _stuck = (_prev_tok_type is not None and
                      self.lexer.current_token.type == _prev_tok_type and
                      self.lexer.current_token.line == _prev_tok_line and
                      self.lexer.current_token.col == _prev_tok_col)
            _prev_tok_type = self.lexer.current_token.type
            _prev_tok_line = self.lexer.current_token.line
            _prev_tok_col = self.lexer.current_token.col
            if _stuck:
                self._diag_advance_safe()
                continue
            if self.lexer.current_token.type in _STATEMENT_STARTERS:
                try:
                    stmt = self._diag_parse_statement()
                    if stmt:
                        statements.append(stmt)
                except RuntimeError as e:
                    self.diag_errors.append((self.lexer.current_token.line, str(e)))
                    self._diag_advance_safe()
            else:
                self.diag_errors.append((self.lexer.current_token.line,
                    f"語法錯誤: 多餘的 {self.lexer.current_token.type}"))
                self._diag_advance_safe()
        return statements

    def _diag_advance_safe(self):
        """Advance lexer while safely handling RuntimeError (e.g. unsupported chars like [ ]).
        
        When advance() raises RuntimeError, current_token is NOT updated,
        which would cause the main loop to hang. Manually skip one char instead.
        """
        try:
            self.lexer.advance()
        except RuntimeError:
            if self.lexer.pos < len(self.lexer.src):
                ch = self.lexer.src[self.lexer.pos]
                self.lexer.pos += 1
                if ch == '\n':
                    self.lexer.line += 1
                    self.lexer.col = 1
                else:
                    self.lexer.col += 1

    def _diag_eat(self, expected_type):
        if self.lexer.current_token.type == expected_type:
            self._diag_advance_safe()
        else:
            tok = self.lexer.current_token
            self.diag_errors.append((tok.line, f"語法錯誤: 期待 {expected_type}，但遇到 {tok.type}"))
            self._diag_advance_safe()

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
            if not self._diag_check_name(self.lexer.current_token):
                self._diag_skip_to_statement()
                return None
            self.lexer.advance()
            self._diag_eat(TokenType.TOK_LPAREN)
            params = []
            while self.lexer.current_token.type not in (TokenType.TOK_RPAREN, TokenType.TOK_EOF):
                param = self.create_node(ASTType.AST_VAR)
                param.name = self.lexer.current_token.value
                self._diag_check_name(self.lexer.current_token)
                self.lexer.advance()
                params.append(param)
                if self.lexer.current_token.type == TokenType.TOK_COMMA:
                    self.lexer.advance()
            self._diag_eat(TokenType.TOK_RPAREN)
            node.left = params
            node.body = self._diag_parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_RETURN:
            ret_line = self.lexer.current_token.line
            self.lexer.advance()
            node = self.create_node(ASTType.AST_RETURN)
            node.line = ret_line
            if self.lexer.current_token.type in _EXPR_STARTERS:
                node.left = self.parse_expression()
                self._diag_check_undeclared_vars(node.left)
            else:
                self.diag_errors.append((ret_line, "語法錯誤: 🔙 後缺少表達式"))
            return node

        elif self.lexer.current_token.type == TokenType.TOK_LET:
            let_line = self.lexer.current_token.line
            self.lexer.advance()
            node = self.create_node(ASTType.AST_LET)
            node.line = let_line
            node.name = self.lexer.current_token.value
            if not self._diag_check_name(self.lexer.current_token):
                self._diag_skip_to_statement()
                return None
            self._declared_vars.add(node.name)
            self.lexer.advance()
            if self.lexer.current_token.type == TokenType.TOK_ASSIGN:
                self.lexer.advance()
                if self.lexer.current_token.type in _EXPR_STARTERS:
                    node.left = self.parse_expression()
                else:
                    self.diag_errors.append((let_line, "語法錯誤: 🟰 後缺少表達式"))
            elif self.lexer.current_token.type in _EXPR_STARTERS and \
                 self.lexer.current_token.line == node.line:
                self.diag_errors.append((self.lexer.current_token.line, "語法錯誤: 缺少 🟰"))
                self.parse_expression()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_PRINT:
            print_line = self.lexer.current_token.line
            self.lexer.advance()
            node = self.create_node(ASTType.AST_PRINT)
            node.line = print_line
            if self.lexer.current_token.type in _EXPR_STARTERS:
                node.left = self.parse_expression()
                self._diag_check_undeclared_vars(node.left)
                if self.lexer.current_token.type in _EXPR_STARTERS and \
                   self.lexer.current_token.line == node.line:
                    self.diag_errors.append((self.lexer.current_token.line, "語法錯誤: 缺少 ➕"))
                    self.parse_expression()
            else:
                self.diag_errors.append((print_line, "語法錯誤: 📢 後缺少表達式"))
            return node

        elif self.lexer.current_token.type == TokenType.TOK_IF:
            if_line = self.lexer.current_token.line
            self.lexer.advance()
            node = self.create_node(ASTType.AST_IF)
            node.line = if_line
            if self.lexer.current_token.type in _EXPR_STARTERS:
                node.left = self.parse_expression()
                self._diag_check_undeclared_vars(node.left)
            else:
                self.diag_errors.append((if_line, "語法錯誤: 🤔 後缺少條件表達式"))
            node.true_branch = self._diag_parse_block()
            if self.lexer.current_token.type == TokenType.TOK_ELSE:
                self.lexer.advance()
                if self.lexer.current_token.type == TokenType.TOK_IF:
                    node.false_branch = [self._diag_parse_statement()]
                else:
                    node.false_branch = self._diag_parse_block()
            return node

        elif self.lexer.current_token.type == TokenType.TOK_WHILE:
            while_line = self.lexer.current_token.line
            self.lexer.advance()
            node = self.create_node(ASTType.AST_WHILE)
            node.line = while_line
            if self.lexer.current_token.type in _EXPR_STARTERS:
                node.left = self.parse_expression()
                self._diag_check_undeclared_vars(node.left)
            else:
                self.diag_errors.append((while_line, "語法錯誤: 🔁 後缺少條件表達式"))
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
            if not self._diag_check_name(self.lexer.current_token):
                self._diag_skip_to_statement()
                return None
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
                if expr.type == ASTType.AST_VAR:
                    self._declared_vars.add(expr.name)
                return node
            elif self.lexer.current_token.type == TokenType.TOK_APPEND:
                self.lexer.advance()
                node = self.create_node(ASTType.AST_APPEND)
                node.left = expr
                node.right = self.parse_expression()
                return node
            if expr.type == ASTType.AST_VAR:
                if expr.name not in self._declared_vars:
                    self.diag_errors.append((expr.line, f"語法錯誤: 未宣告變數「{expr.name}」"))
            elif expr.type in _BARE_EXPR_TYPES:
                self.diag_errors.append((expr.line, "語法錯誤: 少了 📢"))
            if self.lexer.current_token.type in _EXPR_STARTERS and \
               self.lexer.current_token.line == expr.line:
                self.diag_errors.append((expr.line, "語法錯誤: 連續表達式缺少運算子"))
                # Consume remaining expression starters on the same line
                # to avoid cascading the same error for each consecutive expression
                while self.lexer.current_token.type in _EXPR_STARTERS and \
                      self.lexer.current_token.line == expr.line:
                    try:
                        self.parse_expression()
                    except RuntimeError:
                        self.lexer.advance()
            return expr
        except RuntimeError as e:
            self.diag_errors.append((self.lexer.current_token.line, str(e)))
            try:
                self.lexer.advance()
            except RuntimeError:
                pass
            return None

    # NOTE: GUI emolang.py takes only parser.diag_errors[0] (first error)
    # to avoid cascading. The parser may produce multiple errors per session.
    # ── End of diagnostic methods ──

    def parse_statement(self):
        if self.lexer.current_token.type == TokenType.TOK_FUNC:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_FUNC_DEF)
            node.name = self.lexer.current_token.value
            self._check_name(self.lexer.current_token)
            self.lexer.advance()
            self.lexer.eat(TokenType.TOK_LPAREN)
            params = []
            while self.lexer.current_token.type != TokenType.TOK_RPAREN and self.lexer.current_token.type != TokenType.TOK_EOF:
                param = self.create_node(ASTType.AST_VAR)
                param.name = self.lexer.current_token.value
                self._check_name(self.lexer.current_token)
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
            self._check_name(self.lexer.current_token)
            self.lexer.advance()
            if self.lexer.current_token.type == TokenType.TOK_ASSIGN:
                self.lexer.advance()
                node.left = self.parse_expression()
            elif self.lexer.current_token.type in _EXPR_STARTERS and \
                 self.lexer.current_token.line == node.line:
                raise RuntimeError(f"第 {self.lexer.current_token.line} 行: 語法錯誤: 缺少 🟰")
            return node

        elif self.lexer.current_token.type == TokenType.TOK_PRINT:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_PRINT)
            node.left = self.parse_expression()
            if self.lexer.current_token.type in _EXPR_STARTERS and \
               self.lexer.current_token.line == node.line:
                raise RuntimeError(f"第 {self.lexer.current_token.line} 行: 語法錯誤: 缺少 ➕")
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
            self._check_name(self.lexer.current_token)
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
        if expr.type in _BARE_EXPR_TYPES:
            raise RuntimeError(f"第 {expr.line} 行: 語法錯誤: 少了 📢")
        if self.lexer.current_token.type in _EXPR_STARTERS and \
           self.lexer.current_token.line == expr.line:
            raise RuntimeError(f"第 {expr.line} 行: 語法錯誤: 連續表達式缺少運算子")
        return expr