class ASTType:
    AST_LET = "LET"
    AST_ASSIGN = "ASSIGN"
    AST_IF = "IF"
    AST_WHILE = "WHILE"
    AST_FOR = "FOR"
    AST_PRINT = "PRINT"
    AST_BLOCK = "BLOCK"
    AST_BINOP = "BINOP"
    AST_NUM = "NUM"
    AST_STR = "STR"
    AST_VAR = "VAR"
    AST_STRUCT_DEF = "STRUCT_DEF"
    AST_NEW = "NEW"
    AST_DOT = "DOT"
    AST_REF = "REF"
    AST_DEREF = "DEREF"
    AST_ARRAY_ALLOC = "ARRAY_ALLOC"
    AST_INDEX = "INDEX"
    AST_INPUT = "INPUT"
    AST_FLOAT = "FLOAT"
    AST_TRUE = "TRUE"
    AST_FALSE = "FALSE"
    AST_FUNC_DEF = "FUNC_DEF"
    AST_FUNC_CALL = "FUNC_CALL"
    AST_RETURN = "RETURN"


class ASTNode:
    def __init__(self, node_type):
        self.type = node_type
        self.op = None
        self.name = ""
        self.value = 0
        self.f_val = 0.0
        self.left = None
        self.right = None
        self.true_branch = None
        self.false_branch = None
        self.cond = None
        self.step = None
        self.body = None
        self.next = None