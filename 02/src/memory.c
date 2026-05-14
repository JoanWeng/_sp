#include "emolang.h"

// ==========================================
// 1. 實體化所有全域變數 (Global Variables)
// ==========================================
Value memory[MEM_SIZE]; 
int heap_ptr = 1;

StructDef struct_table[50]; 
int struct_count = 0;

FuncDef func_table[50]; 
int func_count = 0;

Symbol sym_stack[20][100]; 
int sym_count[20] = {0}; 
int call_depth = 0;

Value ret_val; 
int is_returning = 0;

// 動態列表與字典記憶體池
ListObj list_pool[100]; 
int list_count = 0;

DictObj dict_pool[100]; 
int dict_count = 0;

// ==========================================
// 2. 輔助函式 (Helper Functions)
// ==========================================

// 寫入字典
void dict_set(int dict_id, const char *key, Value val) {
    DictObj *d = &dict_pool[dict_id];
    for (int i = 0; i < d->count; i++) {
        if (strcmp(d->keys[i], key) == 0) { 
            d->values[i] = val; 
            return; 
        }
    }
    if (d->count < 100) {
        strcpy(d->keys[d->count], key);
        d->values[d->count] = val;
        d->count++;
    } else {
        printf("執行錯誤: 字典容量已滿\n"); exit(1);
    }
}

// 讀取字典
Value dict_get(int dict_id, const char *key) {
    DictObj *d = &dict_pool[dict_id];
    for (int i = 0; i < d->count; i++) {
        if (strcmp(d->keys[i], key) == 0) return d->values[i];
    }
    printf("執行錯誤: 字典找不到鍵值 '%s'\n", key); exit(1);
}

// 記憶體配置
int alloc_mem(int size) { 
    int addr = heap_ptr; 
    heap_ptr += size; 
    return addr; 
}

// 取得變數的記憶體位址 (支援區域與全域變數尋找)
int get_sym_addr(const char *name) {
    // 先找當前區域變數
    for (int i = 0; i < sym_count[call_depth]; i++) {
        if (strcmp(sym_stack[call_depth][i].name, name) == 0) return sym_stack[call_depth][i].addr;
    }
    // 如果找不到，往全域變數找
    if (call_depth > 0) {
        for (int i = 0; i < sym_count[0]; i++) {
            if (strcmp(sym_stack[0][i].name, name) == 0) return sym_stack[0][i].addr;
        }
    }
    printf("執行錯誤: 找不到變數 %s\n", name); exit(1);
}

// 取得賦值對象的記憶體位址或索引
int get_lvalue(ASTNode *node) {
    if (node->type == AST_VAR) return get_sym_addr(node->name);
    else if (node->type == AST_DEREF) return eval(node->left).i;
    else if (node->type == AST_INDEX) {
        Value base = eval(node->left);
        // 如果是動態 List 或 Dict，它們不存在於傳統連續記憶體中，因此禁止使用 📍 (取址符號)
        if (base.type == 3 || base.type == 4) {
            printf("執行錯誤: 無法對動態列表或字典使用 📍 (取址)\n"); exit(1);
        }
        return base.i + eval(node->right).i;
    }
    else if (node->type == AST_DOT) {
        int obj_addr = eval(node->left).i; 
        int sid = memory[obj_addr].i; 
        StructDef *sd = &struct_table[sid];
        for (int i = 0; i < sd->field_count; i++) { 
            if (strcmp(sd->fields[i], node->name) == 0) return obj_addr + 1 + i; 
        }
        printf("執行錯誤: 找不到欄位 %s\n", node->name); exit(1);
    }
    printf("執行錯誤: 無效的賦值對象\n"); exit(1);
}