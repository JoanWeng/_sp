#include "emolang.h"

#define MEM_SIZE 10000
Value memory[MEM_SIZE]; 
int heap_ptr = 1;

// 儲存結構體藍圖
typedef struct { char name[256]; char fields[20][256]; int field_count; } StructDef;
StructDef struct_table[50]; int struct_count = 0;

// 儲存函數藍圖
typedef struct { char name[256]; ASTNode *params; ASTNode *body; } FuncDef;
FuncDef func_table[50]; int func_count = 0;

// 將變數表升級為「堆疊」，支援區域變數
typedef struct { char name[256]; int addr; } Symbol;
Symbol sym_stack[20][100]; // 支援 20 層函數深度，每層 100 個變數
int sym_count[20] = {0}; 
int call_depth = 0; // 0 代表全域 (Global Scope)

// 控制函數回傳中斷的信號
Value ret_val; 
int is_returning = 0;

int alloc_mem(int size) { int addr = heap_ptr; heap_ptr += size; return addr; }

int get_sym_addr(const char *name) {
    // 1. 先從當前的區域變數找
    for (int i = 0; i < sym_count[call_depth]; i++) {
        if (strcmp(sym_stack[call_depth][i].name, name) == 0) return sym_stack[call_depth][i].addr;
    }
    // 2. 如果在函數內找不到，去外面全域(第 0 層)找
    if (call_depth > 0) {
        for (int i = 0; i < sym_count[0]; i++) {
            if (strcmp(sym_stack[0][i].name, name) == 0) return sym_stack[0][i].addr;
        }
    }
    printf("執行錯誤: 找不到變數 %s\n", name); exit(1);
}

int is_truthy(Value v) {
    if (v.type == 0) return v.i != 0;
    if (v.type == 1) return v.f != 0.0;
    if (v.type == 2) return strlen(v.s) > 0;
    return 0;
}

int get_lvalue(ASTNode *node) {
    if (node->type == AST_VAR) return get_sym_addr(node->name);
    else if (node->type == AST_DEREF) return eval(node->left).i;
    else if (node->type == AST_INDEX) return eval(node->left).i + eval(node->right).i;
    else if (node->type == AST_DOT) {
        int obj_addr = eval(node->left).i;
        int sid = memory[obj_addr].i; StructDef *sd = &struct_table[sid];
        for (int i = 0; i < sd->field_count; i++) if (strcmp(sd->fields[i], node->name) == 0) return obj_addr + 1 + i;
        printf("執行錯誤: 找不到欄位 %s\n", node->name); exit(1);
    }
    printf("執行錯誤: 無效的賦值對象\n"); exit(1);
}

Value eval(ASTNode *node) {
    Value res = {0, 0, 0.0, ""};
    if (!node) return res;

    if (node->type == AST_NUM) { res.i = node->value; return res; }
    if (node->type == AST_FLOAT) { res.type = 1; res.f = node->f_val; return res; }
    if (node->type == AST_STR) { res.type = 2; strcpy(res.s, node->name); return res; }
    if (node->type == AST_TRUE) { res.i = 1; return res; }
    if (node->type == AST_FALSE) { res.i = 0; return res; }
    if (node->type == AST_VAR) return memory[get_sym_addr(node->name)];
    if (node->type == AST_REF) { res.i = get_lvalue(node->left); return res; }
    if (node->type == AST_DEREF) return memory[eval(node->left).i];
    if (node->type == AST_INDEX) return memory[get_lvalue(node)];
    
    // 執行函數呼叫
    if (node->type == AST_FUNC_CALL) {
        for (int i = 0; i < func_count; i++) {
            if (strcmp(func_table[i].name, node->name) == 0) {
                FuncDef *fd = &func_table[i];
                
                // 1. 把外面傳進來的值先計算好
                Value arg_vals[20]; int argc = 0;
                ASTNode *arg = node->left;
                while (arg) { arg_vals[argc++] = eval(arg); arg = arg->next; }

                // 2. 潛入下一層 (開闢新的區域變數空間)
                call_depth++;
                sym_count[call_depth] = 0;

                // 3. 註冊參數成為區域變數，並存入數值
                ASTNode *p = fd->params;
                for (int j = 0; j < argc && p; j++) {
                    int addr = alloc_mem(1);
                    strcpy(sym_stack[call_depth][sym_count[call_depth]].name, p->name);
                    sym_stack[call_depth][sym_count[call_depth]].addr = addr;
                    sym_count[call_depth]++;
                    memory[addr] = arg_vals[j];
                    p = p->next;
                }

                // 4. 執行函數內部的所有程式碼
                execute(fd->body);

                // 5. 捕捉 🔙 傳遞出來的回傳值，並重置信號
                if (is_returning) { res = ret_val; is_returning = 0; }
                
                // 6. 浮出水面，回到上一層 (區域變數自動失效)
                call_depth--;
                return res;
            }
        }
        printf("執行錯誤: 找不到函數 %s\n", node->name); exit(1);
    }
    
    if (node->type == AST_INPUT) {
        char in[256]; scanf("%255s", in);
        if (strchr(in, '.')) { res.type = 1; res.f = atof(in); }
        else if (isdigit(in[0]) || (in[0]=='-' && isdigit(in[1]))) { res.type = 0; res.i = atoi(in); }
        else { res.type = 2; strcpy(res.s, in); }
        return res;
    }
    
    if (node->type == AST_ARRAY_ALLOC) { res.i = alloc_mem(eval(node->left).i); return res; }
    if (node->type == AST_NEW) {
        for (int i = 0; i < struct_count; i++) {
            if (strcmp(struct_table[i].name, node->name) == 0) {
                int addr = alloc_mem(1 + struct_table[i].field_count);
                memory[addr].type = 0; memory[addr].i = i; res.i = addr; return res;
            }
        }
        printf("執行錯誤: 找不到結構 %s\n", node->name); exit(1);
    }
    if (node->type == AST_DOT) return memory[get_lvalue(node)];

    if (node->type == AST_BINOP) {
        Value left = eval(node->left); Value right = eval(node->right);
        
        // 支援字串串接
        if (node->op == TOK_PLUS && (left.type == 2 || right.type == 2)) {
            res.type = 2; char l[256] = {0}, r[256] = {0};
            if (left.type == 2) strcpy(l, left.s); else if (left.type == 1) snprintf(l, sizeof(l), "%g", left.f); else snprintf(l, sizeof(l), "%d", left.i);
            if (right.type == 2) strcpy(r, right.s); else if (right.type == 1) snprintf(r, sizeof(r), "%g", right.f); else snprintf(r, sizeof(r), "%d", right.i);
            strncpy(res.s, l, 255); res.s[255] = '\0';
            strncat(res.s, r, 255 - strlen(res.s));
            return res;
        }

        if (left.type == 1 || right.type == 1) {
            res.type = 1; double l_val = (left.type == 1) ? left.f : left.i; double r_val = (right.type == 1) ? right.f : right.i;
            if (node->op == TOK_PLUS) res.f = l_val + r_val; else if (node->op == TOK_MINUS) res.f = l_val - r_val;
            else if (node->op == TOK_MUL) res.f = l_val * r_val; else if (node->op == TOK_DIV) res.f = l_val / r_val;
            else { res.type = 0; if (node->op == TOK_EQ) res.i = l_val == r_val; else if (node->op == TOK_GT) res.i = l_val > r_val; else if (node->op == TOK_LT) res.i = l_val < r_val; }
            return res;
        }
        
        res.type = 0;
        if (node->op == TOK_PLUS) res.i = left.i + right.i; else if (node->op == TOK_MINUS) res.i = left.i - right.i;
        else if (node->op == TOK_MUL) res.i = left.i * right.i; else if (node->op == TOK_DIV) res.i = left.i / right.i;
        else if (node->op == TOK_MOD) res.i = left.i % right.i; else if (node->op == TOK_EQ) res.i = left.i == right.i;
        else if (node->op == TOK_GT) res.i = left.i > right.i; else if (node->op == TOK_LT) res.i = left.i < right.i;
    }
    return res;
}

void execute(ASTNode *stmt) {
    while (stmt != NULL) {
        // 核心更新：如果正在回傳狀態 (🔙)，立刻中斷目前的區塊執行，並一路往外跳脫！
        if (is_returning) return; 

        if (stmt->type == AST_RETURN) {
            ret_val = eval(stmt->left);
            is_returning = 1; // 開啟中斷信號
            return;
        } 
        else if (stmt->type == AST_FUNC_DEF) {
            FuncDef *fd = &func_table[func_count++];
            strcpy(fd->name, stmt->name);
            fd->params = stmt->left;
            fd->body = stmt->body;
        } 
        else if (stmt->type == AST_LET) {
            int addr = alloc_mem(1); 
            // 將變數註冊到當前層級 (call_depth) 的符號堆疊中
            strcpy(sym_stack[call_depth][sym_count[call_depth]].name, stmt->name); 
            sym_stack[call_depth][sym_count[call_depth]].addr = addr; 
            sym_count[call_depth]++;
            if (stmt->left) memory[addr] = eval(stmt->left);
        } 
        else if (stmt->type == AST_ASSIGN) {
            memory[get_lvalue(stmt->left)] = eval(stmt->right);
        } 
        else if (stmt->type == AST_STRUCT_DEF) {
            StructDef *sd = &struct_table[struct_count++]; strcpy(sd->name, stmt->name); sd->field_count = 0;
            ASTNode *field = stmt->body; while (field) { if (field->type == AST_LET) strcpy(sd->fields[sd->field_count++], field->name); field = field->next; }
        } 
        else if (stmt->type == AST_PRINT) {
            Value v = eval(stmt->left);
            if (v.type == 2) printf("%s\n", v.s); else if (v.type == 1) printf("%g\n", v.f); else printf("%d\n", v.i);
        } 
        else if (stmt->type == AST_IF) {
            if (is_truthy(eval(stmt->left))) execute(stmt->true_branch);
            else if (stmt->false_branch) execute(stmt->false_branch);
        } 
        else if (stmt->type == AST_WHILE) {
            while (is_truthy(eval(stmt->left))) execute(stmt->true_branch);
        } 
        else if (stmt->type == AST_FOR) {
            execute(stmt->left); while (is_truthy(eval(stmt->cond))) { execute(stmt->body); execute(stmt->step); }
        }
        
        stmt = stmt->next;
    }
}