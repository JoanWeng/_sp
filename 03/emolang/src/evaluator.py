from tokens import TokenType
from ast import ASTType
from runtime import Value
from lexer import EmoLangLexer
from parser import EmoLangParser


class EmoLangEvaluator:
    def __init__(self):
        self.reset()

    def reset(self):
        self.memory = {}
        self.heap_ptr = 1
        self.struct_table = {}
        self.func_table = {}
        self.sym_stack = [{}]
        self.call_depth = 0
        self.ret_val = Value()
        self.is_returning = False
        self.output = []
        self.input_callback = None
        self.list_pool = []
        self.dict_pool = []

    def alloc_mem(self, size):
        addr = self.heap_ptr
        self.heap_ptr += size
        return addr

    def get_sym_addr(self, name):
        for i in range(len(self.sym_stack) - 1, -1, -1):
            if name in self.sym_stack[i]:
                return self.sym_stack[i][name]
        raise RuntimeError(f"找不到變數 {name}")

    def is_truthy(self, v):
        if v.type == 0:
            return v.i != 0
        elif v.type == 1:
            return v.f != 0.0
        elif v.type == 2:
            return len(v.s) > 0
        return 0

    def assign_value(self, node, val):
        if node.type == ASTType.AST_VAR:
            self.memory[self.get_sym_addr(node.name)] = val
            return
        if node.type == ASTType.AST_DEREF:
            self.memory[self.eval(node.left).i] = val
            return
        if node.type == ASTType.AST_DOT:
            obj_addr = self.eval(node.left).i
            sid = self.memory[obj_addr].i
            sd = self.struct_table[sid]
            field_addr = obj_addr + 1 + sd["fields"].index(node.name)
            self.memory[field_addr] = val
            return
        if node.type == ASTType.AST_INDEX:
            base = self.eval(node.left)
            idx = self.eval(node.right)
            if base.type == 3:
                if idx.i < 0 or idx.i >= self.list_pool[base.i]["count"]:
                    raise RuntimeError("執行錯誤: 列表索引超出範圍")
                self.list_pool[base.i]["items"][idx.i] = val
                return
            if base.type == 4:
                if idx.type != 2:
                    raise RuntimeError("執行錯誤: 字典鍵必須為字串")
                self.dict_set(base.i, idx.s, val)
                return
            self.memory[base.i + idx.i] = val
            return
        raise RuntimeError("無效的賦值對象")

    def get_lvalue(self, node):
        if node.type == ASTType.AST_VAR:
            return self.get_sym_addr(node.name)
        elif node.type == ASTType.AST_DEREF:
            return self.eval(node.left).i
        elif node.type == ASTType.AST_INDEX:
            return self.eval(node.left).i + self.eval(node.right).i
        elif node.type == ASTType.AST_DOT:
            obj_addr = self.eval(node.left).i
            sid = self.memory[obj_addr].i
            sd = self.struct_table[sid]
            field_addr = obj_addr + 1 + sd["fields"].index(node.name)
            return field_addr
        raise RuntimeError("無效的賦值對象")

    def dict_set(self, dict_id, key, val):
        d = self.dict_pool[dict_id]
        for i in range(d["count"]):
            if d["keys"][i] == key:
                d["values"][i] = val
                return
        d["keys"][d["count"]] = key
        d["values"][d["count"]] = val
        d["count"] += 1

    def dict_get(self, dict_id, key):
        d = self.dict_pool[dict_id]
        for i in range(d["count"]):
            if d["keys"][i] == key:
                return d["values"][i]
        raise RuntimeError(f"找不到字典鍵: {key}")

    def eval(self, node):
        if node is None:
            return Value()

        res = Value()

        if node.type == ASTType.AST_NUM:
            res.i = node.value
            return res
        if node.type == ASTType.AST_FLOAT:
            res.type = 1
            res.f = node.f_val
            return res
        if node.type == ASTType.AST_STR:
            res.type = 2
            res.s = node.name
            return res
        if node.type == ASTType.AST_TRUE:
            res.i = 1
            return res
        if node.type == ASTType.AST_FALSE:
            res.i = 0
            return res
        if node.type == ASTType.AST_NOT:
            val = self.eval(node.left)
            res.type = 0
            res.i = 0 if self.is_truthy(val) else 1
            return res
        if node.type == ASTType.AST_VAR:
            return self.memory[self.get_sym_addr(node.name)]
        if node.type == ASTType.AST_REF:
            res.i = self.get_lvalue(node.left)
            return res
        if node.type == ASTType.AST_DEREF:
            return self.memory[self.eval(node.left).i]
        if node.type == ASTType.AST_INDEX:
            base = self.eval(node.left)
            idx = self.eval(node.right)
            if base.type == 3:
                if idx.i < 0 or idx.i >= self.list_pool[base.i]["count"]:
                    raise RuntimeError("執行錯誤: 列表索引超出範圍")
                return self.list_pool[base.i]["items"][idx.i]
            if base.type == 4:
                if idx.type != 2:
                    raise RuntimeError("執行錯誤: 字典鍵必須為字串")
                return self.dict_get(base.i, idx.s)
            return self.memory[base.i + idx.i]

        if node.type == ASTType.AST_NEW_LIST:
            list_id = len(self.list_pool)
            self.list_pool.append({"items": [Value() for _ in range(100)], "count": 0})
            res.type = 3
            res.i = list_id
            return res

        if node.type == ASTType.AST_NEW_DICT:
            dict_id = len(self.dict_pool)
            self.dict_pool.append({"keys": ["" for _ in range(100)], "values": [Value() for _ in range(100)], "count": 0})
            res.type = 4
            res.i = dict_id
            return res

        if node.type == ASTType.AST_LEN:
            target = self.eval(node.left)
            res.type = 0
            if target.type == 2:
                res.i = len(target.s)
            elif target.type == 3:
                res.i = self.list_pool[target.i]["count"]
            elif target.type == 4:
                res.i = self.dict_pool[target.i]["count"]
            else:
                raise RuntimeError("執行錯誤: 該型別沒有長度")
            return res

        if node.type == ASTType.AST_FUNC_CALL:
            if node.name in self.func_table:
                fd = self.func_table[node.name]
                arg_vals = [self.eval(arg) for arg in node.left]

                self.call_depth += 1
                self.sym_stack.append({})

                for j, p in enumerate(fd["params"]):
                    if j < len(arg_vals):
                        addr = self.alloc_mem(1)
                        self.sym_stack[-1][p.name] = addr
                        self.memory[addr] = arg_vals[j]

                self.execute(fd["body"])

                if self.is_returning:
                    res = self.ret_val
                    self.is_returning = False

                self.call_depth -= 1
                self.sym_stack.pop()
                return res
            raise RuntimeError(f"找不到函數 {node.name}")

        if node.type == ASTType.AST_INPUT:
            try:
                if self.input_callback:
                    user_input = self.input_callback()
                else:
                    user_input = input()
            except:
                user_input = ""

            res = Value()
            if '.' in user_input:
                res.type = 1
                res.f = float(user_input) if user_input else 0.0
            elif user_input and user_input.lstrip('-').isdigit():
                res.type = 0
                res.i = int(user_input)
            else:
                res.type = 2
                res.s = user_input
            return res

        if node.type == ASTType.AST_ARRAY_ALLOC:
            res.i = self.alloc_mem(self.eval(node.left).i)
            return res

        if node.type == ASTType.AST_NEW:
            for sid, sd in self.struct_table.items():
                if sd["name"] == node.name:
                    addr = self.alloc_mem(1 + sd["field_count"])
                    v = Value()
                    v.type = 0
                    v.i = sid
                    self.memory[addr] = v
                    res.i = addr
                    return res
            raise RuntimeError(f"找不到結構 {node.name}")

        if node.type == ASTType.AST_DOT:
            return self.memory[self.get_lvalue(node)]

        if node.type == ASTType.AST_BINOP:
            if node.op == TokenType.TOK_AND:
                left = self.eval(node.left)
                if not self.is_truthy(left):
                    res.type = 0
                    res.i = 0
                    return res
                right = self.eval(node.right)
                res.type = 0
                res.i = 1 if self.is_truthy(right) else 0
                return res
            if node.op == TokenType.TOK_OR:
                left = self.eval(node.left)
                if self.is_truthy(left):
                    res.type = 0
                    res.i = 1
                    return res
                right = self.eval(node.right)
                res.type = 0
                res.i = 1 if self.is_truthy(right) else 0
                return res

            left = self.eval(node.left)
            right = self.eval(node.right)

            if node.op == TokenType.TOK_PLUS and (left.type == 2 or right.type == 2):
                res.type = 2
                l = left.s if left.type == 2 else (str(left.f) if left.type == 1 else str(left.i))
                r = right.s if right.type == 2 else (str(right.f) if right.type == 1 else str(right.i))
                res.s = l + r
                return res

            if left.type == 1 or right.type == 1:
                res.type = 1
                l_val = left.f if left.type == 1 else left.i
                r_val = right.f if right.type == 1 else right.i
                if node.op == TokenType.TOK_PLUS:
                    res.f = l_val + r_val
                elif node.op == TokenType.TOK_MINUS:
                    res.f = l_val - r_val
                elif node.op == TokenType.TOK_MUL:
                    res.f = l_val * r_val
                elif node.op == TokenType.TOK_DIV:
                    res.f = l_val / r_val
                elif node.op == TokenType.TOK_EQ:
                    res.type = 0
                    res.i = int(l_val == r_val)
                elif node.op == TokenType.TOK_GT:
                    res.type = 0
                    res.i = int(l_val > r_val)
                elif node.op == TokenType.TOK_LT:
                    res.type = 0
                    res.i = int(l_val < r_val)
                return res

            res.type = 0
            if node.op == TokenType.TOK_PLUS:
                res.i = left.i + right.i
            elif node.op == TokenType.TOK_MINUS:
                res.i = left.i - right.i
            elif node.op == TokenType.TOK_MUL:
                res.i = left.i * right.i
            elif node.op == TokenType.TOK_DIV:
                res.i = left.i // right.i
            elif node.op == TokenType.TOK_MOD:
                res.i = left.i % right.i
            elif node.op == TokenType.TOK_EQ:
                res.i = int(left.i == right.i)
            elif node.op == TokenType.TOK_GT:
                res.i = int(left.i > right.i)
            elif node.op == TokenType.TOK_LT:
                res.i = int(left.i < right.i)
        return res

    def execute(self, statements):
        for stmt in statements:
            if self.is_returning:
                return

            if stmt.type == ASTType.AST_RETURN:
                self.ret_val = self.eval(stmt.left)
                self.is_returning = True
                return

            elif stmt.type == ASTType.AST_FUNC_DEF:
                self.func_table[stmt.name] = {
                    "params": stmt.left,
                    "body": stmt.body
                }

            elif stmt.type == ASTType.AST_LET:
                addr = self.alloc_mem(1)
                self.sym_stack[-1][stmt.name] = addr
                if stmt.left:
                    self.memory[addr] = self.eval(stmt.left)

            elif stmt.type == ASTType.AST_ASSIGN:
                self.assign_value(stmt.left, self.eval(stmt.right))

            elif stmt.type == ASTType.AST_APPEND:
                list_val = self.eval(stmt.left)
                if list_val.type != 3:
                    raise RuntimeError("執行錯誤: 只能對列表使用 🛒 (追加)")
                val = self.eval(stmt.right)
                l = self.list_pool[list_val.i]
                if l["count"] < 100:
                    l["items"][l["count"]] = val
                    l["count"] += 1
                else:
                    raise RuntimeError("執行錯誤: 列表容量已滿")

            elif stmt.type == ASTType.AST_STRUCT_DEF:
                sid = len(self.struct_table)
                fields = []
                if stmt.body:
                    for field in stmt.body:
                        if field.type == ASTType.AST_LET:
                            fields.append(field.name)
                self.struct_table[sid] = {
                    "name": stmt.name,
                    "fields": fields,
                    "field_count": len(fields)
                }

            elif stmt.type == ASTType.AST_PRINT:
                v = self.eval(stmt.left)
                if v.type == 3:
                    items = []
                    l = self.list_pool[v.i]
                    for idx in range(l["count"]):
                        item = l["items"][idx]
                        if item.type == 2:
                            items.append(f'"{item.s}"')
                        elif item.type == 1:
                            items.append(str(item.f))
                        else:
                            items.append(str(item.i))
                    self.output.append("[" + ", ".join(items) + "]")
                elif v.type == 4:
                    pairs = []
                    d = self.dict_pool[v.i]
                    for idx in range(d["count"]):
                        val = d["values"][idx]
                        if val.type == 2:
                            val_str = f'"{val.s}"'
                        elif val.type == 1:
                            val_str = str(val.f)
                        else:
                            val_str = str(val.i)
                        pairs.append(f'"{d["keys"][idx]}": {val_str}')
                    self.output.append("{" + ", ".join(pairs) + "}")
                elif v.type == 2:
                    self.output.append(v.s)
                elif v.type == 1:
                    self.output.append(str(v.f))
                else:
                    self.output.append(str(v.i))

            elif stmt.type == ASTType.AST_IF:
                if self.is_truthy(self.eval(stmt.left)):
                    self.execute(stmt.true_branch)
                elif stmt.false_branch:
                    self.execute(stmt.false_branch)

            elif stmt.type == ASTType.AST_WHILE:
                while self.is_truthy(self.eval(stmt.left)):
                    self.execute(stmt.true_branch)

            elif stmt.type == ASTType.AST_FOR:
                self.execute([stmt.left])
                while self.is_truthy(self.eval(stmt.cond)):
                    self.execute(stmt.body)
                    self.execute([stmt.step])

    def run(self, code, input_callback=None):
        self.reset()
        self.input_callback = input_callback

        lexer = EmoLangLexer(code)
        parser = EmoLangParser(lexer)
        statements = parser.parse()
        self.execute(statements)

        return "\n".join(self.output)