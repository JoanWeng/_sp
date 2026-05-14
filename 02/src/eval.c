#include "emolang.h"

// 判斷 Value 是否為 True (布林邏輯)
int is_truthy(Value v) {
    if (v.type == 0) return v.i != 0;
    if (v.type == 1) return v.f != 0.0;
    if (v.type == 2) return strlen(v.s) > 0;
    return 0;
}

// 統一的變數/屬性/陣列寫入機制 (賦值引擎)
void assign_value(ASTNode *node, Value val) {
    if (node->type == AST_VAR) { 
        memory[get_sym_addr(node->name)] = val; 
        return; 
    }
    if (node->type == AST_DEREF) { 
        memory[eval(node->left).i] = val; 
        return; 
    }
    if (node->type == AST_DOT) {
        int obj_addr = eval(node->left).i; 
        int sid = memory[obj_addr].i; 
        StructDef *sd = &struct_table[sid];
        for (int i = 0; i < sd->field_count; i++) {
            if (strcmp(sd->fields[i], node->name) == 0) { 
                memory[obj_addr + 1 + i] = val; 
                return; 
            }
        }
        printf("執行錯誤: 找不到結構體欄位 %s\n", node->name); exit(1);
    }
    if (node->type == AST_INDEX) {
        Value base = eval(node->left);
        Value idx = eval(node->right);
        
        if (base.type == 3) { // 寫入 List (📋)
            if (idx.i < 0 || idx.i >= list_pool[base.i].count) { 
                printf("執行錯誤: 列表索引超出範圍\n"); exit(1); 
            }
            list_pool[base.i].items[idx.i] = val; 
            return;
        }
        if (base.type == 4) { // 寫入 Dict (📖)
            if (idx.type != 2) { 
                printf("執行錯誤: 字典鍵必須為字串\n"); exit(1); 
            }
            dict_set(base.i, idx.s, val); 
            return;
        }
        // 寫入一般陣列
        memory[base.i + idx.i] = val; 
        return; 
    }
    printf("執行錯誤: 無效的賦值對象\n"); exit(1);
}

// 表達式求值 (遞迴計算樹狀結構的值)
Value eval(ASTNode *node) {
    Value res = {0, 0, 0.0, ""};
    if (!node) return res;

    // 邏輯 NOT
    if (node->type == AST_NOT) {
        res.type = 0; res.i = !is_truthy(eval(node->left)); return res;
    }

    // 基礎值
    if (node->type == AST_NUM) { res.i = node->value; return res; }
    if (node->type == AST_FLOAT) { res.type = 1; res.f = node->f_val; return res; }
    if (node->type == AST_STR) { res.type = 2; strcpy(res.s, node->name); return res; }
    if (node->type == AST_TRUE) { res.i = 1; return res; }
    if (node->type == AST_FALSE) { res.i = 0; return res; }
    
    // 變數與指標讀取
    if (node->type == AST_VAR) return memory[get_sym_addr(node->name)];
    if (node->type == AST_REF) { res.i = get_lvalue(node->left); return res; }
    if (node->type == AST_DEREF) return memory[eval(node->left).i];
    
    // 陣列 / 列表 / 字典讀取
    if (node->type == AST_INDEX) {
        Value base = eval(node->left);
        Value idx = eval(node->right);
        if (base.type == 3) {
            if (idx.i < 0 || idx.i >= list_pool[base.i].count) { 
                printf("執行錯誤: 列表索引超出範圍\n"); exit(1); 
            }
            return list_pool[base.i].items[idx.i];
        }
        if (base.type == 4) {
            if (idx.type != 2) { 
                printf("執行錯誤: 字典的鍵必須為字串\n"); exit(1); 
            }
            return dict_get(base.i, idx.s);
        }
        return memory[base.i + idx.i];
    }
    
    // 建立動態列表與字典
    if (node->type == AST_NEW_LIST) { 
        res.type = 3; res.i = list_count++; 
        list_pool[res.i].count = 0; 
        return res; 
    }
    if (node->type == AST_NEW_DICT) { 
        res.type = 4; res.i = dict_count++; 
        dict_pool[res.i].count = 0; 
        return res; 
    }
    
    // 計算長度
    if (node->type == AST_LEN) {
        Value target = eval(node->left); res.type = 0;
        if (target.type == 2) res.i = strlen(target.s);
        else if (target.type == 3) res.i = list_pool[target.i].count;
        else if (target.type == 4) res.i = dict_pool[target.i].count;
        else { printf("執行錯誤: 該型別沒有長度\n"); exit(1); }
        return res;
    }
    
    // 函數呼叫 (區域變數管理)
    if (node->type == AST_FUNC_CALL) {
        for (int i = 0; i < func_count; i++) {
            if (strcmp(func_table[i].name, node->name) == 0) {
                FuncDef *fd = &func_table[i];
                Value arg_vals[20]; int argc = 0;
                ASTNode *arg = node->left;
                while (arg) { arg_vals[argc++] = eval(arg); arg = arg->next; }

                call_depth++; 
                sym_count[call_depth] = 0;

                ASTNode *p = fd->params;
                for (int j = 0; j < argc && p; j++) {
                    int addr = alloc_mem(1);
                    strcpy(sym_stack[call_depth][sym_count[call_depth]].name, p->name);
                    sym_stack[call_depth][sym_count[call_depth]].addr = addr;
                    sym_count[call_depth]++;
                    memory[addr] = arg_vals[j];
                    p = p->next;
                }

                execute(fd->body);
                if (is_returning) { res = ret_val; is_returning = 0; }
                call_depth--;
                return res;
            }
        }
        printf("執行錯誤: 找不到函數 %s\n", node->name); exit(1);
    }
    
    // 終端機輸入
    if (node->type == AST_INPUT) {
        char in[256]; scanf("%255s", in);
        if (strchr(in, '.')) { res.type = 1; res.f = atof(in); }
        else if (isdigit(in[0]) || (in[0]=='-' && isdigit(in[1]))) { res.type = 0; res.i = atoi(in); }
        else { res.type = 2; strcpy(res.s, in); }
        return res;
    }
    
    // 動態配置與結構
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

    // 雙元運算子 (算術、邏輯)
    if (node->type == AST_BINOP) {
        // 短路求值
        if (node->op == TOK_AND) {
            Value left = eval(node->left);
            if (!is_truthy(left)) { left.type = 0; left.i = 0; return left; }
            Value right = eval(node->right); right.type = 0; right.i = is_truthy(right); return right;
        }
        if (node->op == TOK_OR) {
            Value left = eval(node->left);
            if (is_truthy(left)) { left.type = 0; left.i = 1; return left; }
            Value right = eval(node->right); right.type = 0; right.i = is_truthy(right); return right;
        }
        
        // 算出左右兩邊的值
        Value left = eval(node->left); 
        Value right = eval(node->right);
        
        // 字串串接
        if (node->op == TOK_PLUS && (left.type == 2 || right.type == 2)) {
            res.type = 2; char l[256] = {0}, r[256] = {0};
            if (left.type == 2) strcpy(l, left.s); else if (left.type == 1) snprintf(l, sizeof(l), "%g", left.f); else snprintf(l, sizeof(l), "%d", left.i);
            if (right.type == 2) strcpy(r, right.s); else if (right.type == 1) snprintf(r, sizeof(r), "%g", right.f); else snprintf(r, sizeof(r), "%d", right.i);
            strncpy(res.s, l, 255); res.s[255] = '\0'; strncat(res.s, r, 255 - strlen(res.s));
            return res;
        }

        // 小數點計算
        if (left.type == 1 || right.type == 1) {
            res.type = 1; double l_val = (left.type == 1) ? left.f : left.i; double r_val = (right.type == 1) ? right.f : right.i;
            if (node->op == TOK_PLUS) res.f = l_val + r_val; else if (node->op == TOK_MINUS) res.f = l_val - r_val;
            else if (node->op == TOK_MUL) res.f = l_val * r_val; else if (node->op == TOK_DIV) res.f = l_val / r_val;
            else { res.type = 0; if (node->op == TOK_EQ) res.i = l_val == r_val; else if (node->op == TOK_GT) res.i = l_val > r_val; else if (node->op == TOK_LT) res.i = l_val < r_val; }
            return res;
        }
        
        // 整數計算
        res.type = 0;
        if (node->op == TOK_PLUS) res.i = left.i + right.i; else if (node->op == TOK_MINUS) res.i = left.i - right.i;
        else if (node->op == TOK_MUL) res.i = left.i * right.i; else if (node->op == TOK_DIV) res.i = left.i / right.i;
        else if (node->op == TOK_MOD) res.i = left.i % right.i; else if (node->op == TOK_EQ) res.i = left.i == right.i;
        else if (node->op == TOK_GT) res.i = left.i > right.i; else if (node->op == TOK_LT) res.i = left.i < right.i;
    }
    return res;
}

// 完美的印出函式 (支援陣列 [ ] 與 字典 { })
void print_value(Value v) {
    if (v.type == 3) {
        printf("[");
        for (int i = 0; i < list_pool[v.i].count; i++) {
            Value item = list_pool[v.i].items[i];
            if (item.type == 2) printf("\"%s\"", item.s); 
            else if (item.type == 1) printf("%g", item.f); 
            else printf("%d", item.i);
            
            if (i < list_pool[v.i].count - 1) printf(", ");
        }
        printf("]\n");
    } else if (v.type == 4) {
        printf("{");
        for (int i = 0; i < dict_pool[v.i].count; i++) {
            Value item = dict_pool[v.i].values[i];
            printf("\"%s\": ", dict_pool[v.i].keys[i]);
            
            if (item.type == 2) printf("\"%s\"", item.s); 
            else if (item.type == 1) printf("%g", item.f); 
            else printf("%d", item.i);
            
            if (i < dict_pool[v.i].count - 1) printf(", ");
        }
        printf("}\n");
    } 
    else if (v.type == 2) printf("%s\n", v.s); 
    else if (v.type == 1) printf("%g\n", v.f); 
    else printf("%d\n", v.i);
}

// 執行 AST 的主邏輯
void execute(ASTNode *stmt) {
    while (stmt != NULL) {
        if (is_returning) return; // 遇到 return，中斷執行區塊

        if (stmt->type == AST_RETURN) {
            ret_val = eval(stmt->left); is_returning = 1; return;
        } 
        else if (stmt->type == AST_FUNC_DEF) {
            FuncDef *fd = &func_table[func_count++];
            strcpy(fd->name, stmt->name); fd->params = stmt->left; fd->body = stmt->body;
        } 
        else if (stmt->type == AST_LET) {
            int addr = alloc_mem(1); 
            strcpy(sym_stack[call_depth][sym_count[call_depth]].name, stmt->name); 
            sym_stack[call_depth][sym_count[call_depth]].addr = addr; 
            sym_count[call_depth]++;
            if (stmt->left) memory[addr] = eval(stmt->left);
        } 
        else if (stmt->type == AST_ASSIGN) {
            assign_value(stmt->left, eval(stmt->right)); // 使用強大的 assign_value
        } 
        else if (stmt->type == AST_APPEND) { // 將資料推入 List 🛒
            Value list = eval(stmt->left);
            if (list.type != 3) { printf("執行錯誤: 只能對列表使用 🛒 (追加)\n"); exit(1); }
            Value val = eval(stmt->right);
            ListObj *l = &list_pool[list.i];
            if (l->count < 100) l->items[l->count++] = val;
            else { printf("執行錯誤: 列表容量已滿\n"); exit(1); }
        }
        else if (stmt->type == AST_STRUCT_DEF) {
            StructDef *sd = &struct_table[struct_count++]; strcpy(sd->name, stmt->name); sd->field_count = 0;
            ASTNode *field = stmt->body; 
            while (field) { 
                if (field->type == AST_LET) strcpy(sd->fields[sd->field_count++], field->name); 
                field = field->next; 
            }
        } 
        else if (stmt->type == AST_PRINT) {
            print_value(eval(stmt->left)); // 使用強大的 print_value
        } 
        else if (stmt->type == AST_IF) {
            if (is_truthy(eval(stmt->left))) execute(stmt->true_branch);
            else if (stmt->false_branch) execute(stmt->false_branch);
        } 
        else if (stmt->type == AST_WHILE) {
            while (is_truthy(eval(stmt->left))) execute(stmt->true_branch);
        } 
        else if (stmt->type == AST_FOR) {
            execute(stmt->left); 
            while (is_truthy(eval(stmt->cond))) { 
                execute(stmt->body); 
                execute(stmt->step); 
            }
        }
        
        stmt = stmt->next;
    }
}