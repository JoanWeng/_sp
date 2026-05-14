from tokens import TokenType
from ast import ASTType, ASTNode
from lexer import EmoLangLexer


class EmoLangParser:
    def __init__(self, lexer):
        self.lexer = lexer

    def create_node(self, ast_type):
        return ASTNode(ast_type)

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

    def parse_prefix(self):
        if self.lexer.current_token.type == TokenType.TOK_NOT:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_NOT)
            node.left = self.parse_prefix()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_INPUT:
            self.lexer.advance()
            return self.create_node(ASTType.AST_INPUT)
        elif self.lexer.current_token.type == TokenType.TOK_REF:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_REF)
            node.left = self.parse_prefix()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_DEREF:
            self.lexer.advance()
            node = self.create_node(ASTType.AST_DEREF)
            node.left = self.parse_prefix()
            return node
        elif self.lexer.current_token.type == TokenType.TOK_NEW:
            self.lexer.advance()
            if self.lexer.current_token.type == TokenType.TOK_ARRAY:
                self.lexer.advance()
                node = self.create_node(ASTType.AST_ARRAY_ALLOC)
                node.left = self.parse_primary()
                return node
            else:
                node = self.create_node(ASTType.AST_NEW)
                node.name = self.lexer.current_token.value
                self.lexer.advance()
                return node
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
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
        return expr