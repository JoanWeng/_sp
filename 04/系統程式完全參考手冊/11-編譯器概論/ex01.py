# ============================================================
#  第 11 章　習題 01 — 迷你編譯器管線模擬
#  實作：詞法分析 → 語法分析（AST）→ 三位址碼產生 → 最佳化
#        示範完整的編譯前端流程
# ============================================================

from dataclasses import dataclass, field
from typing import Any


# ══════════════════════════════════════════════════════════════
#  第一階段：詞法分析器（Lexer）
# ══════════════════════════════════════════════════════════════

KEYWORDS = {'int', 'float', 'if', 'else', 'while', 'return', 'void'}

@dataclass
class Token:
    kind:  str
    value: str
    line:  int = 0

def lex(source: str) -> list[Token]:
    tokens = []
    i = 0
    line = 1
    while i < len(source):
        c = source[i]

        if c == '\n':
            line += 1; i += 1; continue
        if c.isspace():
            i += 1; continue

        # 單行註解
        if c == '/' and i+1 < len(source) and source[i+1] == '/':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue

        # 識別符 / 關鍵字
        if c.isalpha() or c == '_':
            j = i
            while j < len(source) and (source[j].isalnum() or source[j] == '_'):
                j += 1
            word = source[i:j]
            tokens.append(Token('KEYWORD' if word in KEYWORDS else 'IDENT', word, line))
            i = j; continue

        # 數字
        if c.isdigit():
            j = i
            is_float = False
            while j < len(source) and (source[j].isdigit() or source[j] == '.'):
                if source[j] == '.': is_float = True
                j += 1
            tokens.append(Token('FLOAT_LIT' if is_float else 'INT_LIT', source[i:j], line))
            i = j; continue

        # 雙字元運算子
        two = source[i:i+2]
        if two in ('==', '!=', '<=', '>=', '&&', '||', '+=', '-=', '*='):
            tokens.append(Token('OP', two, line)); i += 2; continue

        # 單字元
        single_map = {
            '+':'OP', '-':'OP', '*':'OP', '/':'OP', '%':'OP',
            '<':'OP', '>':'OP', '=':'ASSIGN',
            ';':'SEMI', ',':'COMMA',
            '(':'LPAREN', ')':'RPAREN',
            '{':'LBRACE', '}':'RBRACE',
        }
        if c in single_map:
            tokens.append(Token(single_map[c], c, line)); i += 1; continue

        raise SyntaxError(f"行 {line}: 未知字元 '{c}'")

    tokens.append(Token('EOF', '', line))
    return tokens


# ══════════════════════════════════════════════════════════════
#  第二階段：語法分析器（Recursive Descent Parser）
# ══════════════════════════════════════════════════════════════

@dataclass
class ASTNode:
    kind:     str
    value:    Any              = None
    children: list             = field(default_factory=list)

    def __repr__(self):
        if self.children:
            return f"{self.kind}({self.value}, [{', '.join(repr(c) for c in self.children)}])"
        return f"{self.kind}({self.value!r})"

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos    = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, kind: str, value: str = None) -> Token:
        t = self.advance()
        if t.kind != kind or (value and t.value != value):
            raise SyntaxError(f"預期 {kind}({value})，得到 {t.kind}({t.value!r})")
        return t

    def match(self, kind: str, value: str = None) -> bool:
        t = self.peek()
        return t.kind == kind and (value is None or t.value == value)

    # ── 文法規則 ──────────────────────────────────────────────

    def parse_program(self) -> ASTNode:
        stmts = []
        while not self.match('EOF'):
            stmts.append(self.parse_stmt())
        return ASTNode('Program', children=stmts)

    def parse_stmt(self) -> ASTNode:
        # 變數宣告：int/float IDENT [= expr] ;
        if self.match('KEYWORD') and self.peek().value in ('int', 'float'):
            return self.parse_decl()
        # if 語句
        if self.match('KEYWORD', 'if'):
            return self.parse_if()
        # while 語句
        if self.match('KEYWORD', 'while'):
            return self.parse_while()
        # return 語句
        if self.match('KEYWORD', 'return'):
            return self.parse_return()
        # block
        if self.match('LBRACE'):
            return self.parse_block()
        # 運算式語句
        expr = self.parse_expr()
        self.expect('SEMI')
        return ASTNode('ExprStmt', children=[expr])

    def parse_decl(self) -> ASTNode:
        dtype = self.advance().value     # int / float
        name  = self.expect('IDENT').value
        init  = None
        if self.match('ASSIGN'):
            self.advance()
            init = self.parse_expr()
        self.expect('SEMI')
        children = [ASTNode('Type', dtype)]
        if init:
            children.append(init)
        return ASTNode('Decl', name, children)

    def parse_if(self) -> ASTNode:
        self.expect('KEYWORD', 'if')
        self.expect('LPAREN')
        cond = self.parse_expr()
        self.expect('RPAREN')
        then = self.parse_stmt()
        else_ = None
        if self.match('KEYWORD', 'else'):
            self.advance()
            else_ = self.parse_stmt()
        children = [cond, then] + ([else_] if else_ else [])
        return ASTNode('If', children=children)

    def parse_while(self) -> ASTNode:
        self.expect('KEYWORD', 'while')
        self.expect('LPAREN')
        cond = self.parse_expr()
        self.expect('RPAREN')
        body = self.parse_stmt()
        return ASTNode('While', children=[cond, body])

    def parse_return(self) -> ASTNode:
        self.expect('KEYWORD', 'return')
        expr = self.parse_expr()
        self.expect('SEMI')
        return ASTNode('Return', children=[expr])

    def parse_block(self) -> ASTNode:
        self.expect('LBRACE')
        stmts = []
        while not self.match('RBRACE'):
            stmts.append(self.parse_stmt())
        self.expect('RBRACE')
        return ASTNode('Block', children=stmts)

    def parse_expr(self) -> ASTNode:
        return self.parse_assign()

    def parse_assign(self) -> ASTNode:
        left = self.parse_compare()
        if self.match('ASSIGN'):
            op = self.advance().value
            right = self.parse_assign()
            return ASTNode('Assign', op, [left, right])
        return left

    def parse_compare(self) -> ASTNode:
        left = self.parse_add()
        while self.match('OP') and self.peek().value in ('<', '>', '==', '!=', '<=', '>='):
            op = self.advance().value
            right = self.parse_add()
            left = ASTNode('BinOp', op, [left, right])
        return left

    def parse_add(self) -> ASTNode:
        left = self.parse_mul()
        while self.match('OP') and self.peek().value in ('+', '-'):
            op = self.advance().value
            right = self.parse_mul()
            left = ASTNode('BinOp', op, [left, right])
        return left

    def parse_mul(self) -> ASTNode:
        left = self.parse_unary()
        while self.match('OP') and self.peek().value in ('*', '/', '%'):
            op = self.advance().value
            right = self.parse_unary()
            left = ASTNode('BinOp', op, [left, right])
        return left

    def parse_unary(self) -> ASTNode:
        if self.match('OP', '-'):
            self.advance()
            operand = self.parse_primary()
            return ASTNode('Unary', '-', [operand])
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        t = self.peek()
        if t.kind == 'INT_LIT':
            self.advance()
            return ASTNode('IntLit', int(t.value))
        if t.kind == 'FLOAT_LIT':
            self.advance()
            return ASTNode('FloatLit', float(t.value))
        if t.kind == 'IDENT':
            self.advance()
            # 函式呼叫
            if self.match('LPAREN'):
                self.advance()
                args = []
                while not self.match('RPAREN'):
                    args.append(self.parse_expr())
                    if self.match('COMMA'):
                        self.advance()
                self.expect('RPAREN')
                return ASTNode('Call', t.value, args)
            return ASTNode('Var', t.value)
        if t.kind == 'LPAREN':
            self.advance()
            expr = self.parse_expr()
            self.expect('RPAREN')
            return expr
        raise SyntaxError(f"行 {t.line}: 意外的 Token {t.kind}({t.value!r})")


# ── AST 印出 ──────────────────────────────────────────────────

def print_ast(node: ASTNode, indent: int = 0):
    prefix = "  " * indent
    val    = f" [{node.value!r}]" if node.value is not None else ""
    print(f"{prefix}{node.kind}{val}")
    for child in node.children:
        print_ast(child, indent + 1)


# ══════════════════════════════════════════════════════════════
#  第三階段：三位址碼產生器（TAC Generator）
# ══════════════════════════════════════════════════════════════

class TACGen:
    def __init__(self):
        self.instrs:  list[str] = []
        self._tmp    = 0
        self._label  = 0

    def new_tmp(self) -> str:
        t = f"t{self._tmp}"
        self._tmp += 1
        return t

    def new_label(self) -> str:
        l = f"L{self._label}"
        self._label += 1
        return l

    def emit(self, instr: str):
        self.instrs.append(instr)

    def label(self, name: str):
        self.instrs.append(f"{name}:")

    def gen(self, node: ASTNode) -> str | None:
        k = node.kind

        if k == 'Program':
            for child in node.children:
                self.gen(child)
            return None

        if k == 'Block':
            for child in node.children:
                self.gen(child)
            return None

        if k == 'Decl':
            if len(node.children) > 1:   # 有初始化
                val = self.gen(node.children[1])
                self.emit(f"  {node.value} = {val}")
            else:
                self.emit(f"  {node.value} = 0      // 未初始化")
            return node.value

        if k == 'ExprStmt':
            self.gen(node.children[0])
            return None

        if k == 'Assign':
            rval = self.gen(node.children[1])
            lval = node.children[0].value
            self.emit(f"  {lval} = {rval}")
            return lval

        if k == 'BinOp':
            left  = self.gen(node.children[0])
            right = self.gen(node.children[1])
            tmp   = self.new_tmp()
            self.emit(f"  {tmp} = {left} {node.value} {right}")
            return tmp

        if k == 'Unary':
            operand = self.gen(node.children[0])
            tmp     = self.new_tmp()
            self.emit(f"  {tmp} = -{operand}")
            return tmp

        if k == 'If':
            cond      = self.gen(node.children[0])
            l_else    = self.new_label()
            l_end     = self.new_label()
            op        = node.children[0].value if node.children[0].kind == 'BinOp' else '!='
            neg_op    = {'<':'>=', '>':'<=', '==':'!=', '!=':'==',
                         '<=':'>','>=':'<'}.get(op, '==')
            if node.children[0].kind == 'BinOp':
                left  = node.children[0].children[0].value or 't?'
                right = node.children[0].children[1].value if node.children[0].children[1].value is not None else 't?'
                self.emit(f"  if {left} {neg_op} {right} goto {l_else}")
            else:
                self.emit(f"  if {cond} == 0 goto {l_else}")
            self.gen(node.children[1])   # then
            if len(node.children) > 2:
                self.emit(f"  goto {l_end}")
            self.label(l_else)
            if len(node.children) > 2:
                self.gen(node.children[2])   # else
                self.label(l_end)
            return None

        if k == 'While':
            l_top = self.new_label()
            l_end = self.new_label()
            self.label(l_top)
            cond  = self.gen(node.children[0])
            if node.children[0].kind == 'BinOp':
                c = node.children[0]
                left  = c.children[0].value or 't?'
                right = c.children[1].value if c.children[1].value is not None else 't?'
                neg   = {'<':'>=','>':'<=','==':'!=','!=':'==','<=':'>','>=':'<'}.get(c.value,'==')
                self.emit(f"  if {left} {neg} {right} goto {l_end}")
            else:
                self.emit(f"  if {cond} == 0 goto {l_end}")
            self.gen(node.children[1])   # body
            self.emit(f"  goto {l_top}")
            self.label(l_end)
            return None

        if k == 'Return':
            val = self.gen(node.children[0])
            self.emit(f"  return {val}")
            return None

        if k == 'Call':
            for i, arg in enumerate(node.children):
                v = self.gen(arg)
                self.emit(f"  param {v}")
            tmp = self.new_tmp()
            self.emit(f"  {tmp} = call {node.value}, {len(node.children)}")
            return tmp

        if k == 'Var':
            return node.value

        if k in ('IntLit', 'FloatLit'):
            return str(node.value)

        return None


# ══════════════════════════════════════════════════════════════
#  第四階段：簡易最佳化（常數摺疊 + 死碼消除）
# ══════════════════════════════════════════════════════════════

def optimize_constant_folding(instrs: list[str]) -> list[str]:
    """常數摺疊：t0 = 2 + 3 → t0 = 5"""
    result = []
    for instr in instrs:
        import re
        m = re.match(r'(\s+)(\w+) = (\d+(?:\.\d+)?) ([+\-*/]) (\d+(?:\.\d+)?)', instr)
        if m:
            pre, tmp, a, op, b = m.groups()
            a, b = float(a), float(b)
            val = {'+':(a+b), '-':(a-b), '*':(a*b), '/':(a/b if b else float('inf'))}[op]
            val_s = str(int(val)) if val == int(val) else str(val)
            result.append(f"{pre}{tmp} = {val_s}  // 常數摺疊: {a}{op}{b}")
        else:
            result.append(instr)
    return result

def optimize_dead_code(instrs: list[str]) -> list[str]:
    """死碼消除：移除定義後從未被使用的臨時變數"""
    import re
    used = set()
    for instr in instrs:
        for m in re.finditer(r'\b(t\d+|[a-zA-Z_]\w*)\b', instr.split('=', 1)[-1] if '=' in instr else instr):
            used.add(m.group(1))

    result = []
    for instr in instrs:
        m = re.match(r'\s+(\w+) = ', instr)
        if m:
            var = m.group(1)
            if var.startswith('t') and var not in used:
                result.append(f"  // 死碼消除: {instr.strip()}")
                continue
        result.append(instr)
    return result


# ── 主程式 ────────────────────────────────────────────────────

def compile_and_show(source: str, title: str):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")
    print(f"\n  原始程式碼：")
    for i, line in enumerate(source.strip().splitlines(), 1):
        print(f"    {i:>2}: {line}")

    # 詞法分析
    tokens = lex(source)
    print(f"\n  詞法分析（Token 串流）：")
    for t in tokens:
        if t.kind != 'EOF':
            print(f"    ({t.kind:<12}, {t.value!r})")

    # 語法分析
    parser = Parser(tokens)
    ast    = parser.parse_program()
    print(f"\n  語法分析（AST）：")
    print_ast(ast, indent=2)

    # TAC 產生
    gen = TACGen()
    gen.gen(ast)
    print(f"\n  三位址碼（TAC）：")
    for instr in gen.instrs:
        print(f"  {instr}")

    # 最佳化
    opt1 = optimize_constant_folding(gen.instrs)
    opt2 = optimize_dead_code(opt1)
    changed = any(a != b for a, b in zip(gen.instrs, opt2))
    if changed:
        print(f"\n  最佳化後 TAC：")
        for instr in opt2:
            print(f"  {instr}")


if __name__ == "__main__":
    # 示範 1：基本運算式
    compile_and_show(
        "int x = 2 + 3 * 4;",
        "示範 1：基本運算式（含常數摺疊）"
    )

    # 示範 2：if-else
    compile_and_show("""\
int a = 10;
int b = 20;
if (a < b) {
    int result = b - a;
} else {
    int result = a - b;
}""",
        "示範 2：if-else 翻譯"
    )

    # 示範 3：while 迴圈
    compile_and_show("""\
int sum = 0;
int i = 1;
while (i <= 10) {
    sum = sum + i;
    i = i + 1;
}""",
        "示範 3：while 迴圈（計算 1+2+...+10）"
    )