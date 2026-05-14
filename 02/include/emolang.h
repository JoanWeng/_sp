#ifndef EMOLANG_H
#define EMOLANG_H

#include "io.h"
#include "utils.h"

#define MEM_SIZE 10000

// 1. 基礎型別定義
typedef enum {
    TOK_LET, TOK_ASSIGN, TOK_IF, TOK_ELSE, TOK_WHILE, TOK_FOR,
    TOK_LBRACE, TOK_RBRACE, TOK_SEP, TOK_PRINT,
    TOK_PLUS, TOK_MINUS, TOK_MUL, TOK_DIV, TOK_MOD,
    TOK_EQ, TOK_GT, TOK_LT,
    TOK_STRUCT, TOK_NEW, TOK_DOT, TOK_REF, TOK_DEREF,
    TOK_ARRAY, TOK_INDEX, TOK_INPUT, TOK_LPAREN, TOK_RPAREN, TOK_COMMA,
    TOK_NUM, TOK_FLOAT_NUM, TOK_TRUE, TOK_FALSE, TOK_STR, TOK_ID,
    TOK_FUNC, TOK_RETURN, TOK_AND, TOK_OR, TOK_NOT,
    TOK_LIST, TOK_DICT, TOK_APPEND, TOK_LEN, TOK_EOF // 新增列表與字典 Tokens
} TokenType;

typedef struct { TokenType type; char value[256]; } Token;

// type 0:整數/布林, 1:小數, 2:字串, 3:列表(ID), 4:字典(ID)
typedef struct { int type; int i; double f; char s[256]; } Value;

// 2. 抽象語法樹 (AST)
typedef enum {
    AST_LET, AST_ASSIGN, AST_IF, AST_WHILE, AST_FOR, AST_PRINT,
    AST_BLOCK, AST_BINOP, AST_NUM, AST_STR, AST_VAR,
    AST_STRUCT_DEF, AST_NEW, AST_DOT, AST_REF, AST_DEREF,
    AST_ARRAY_ALLOC, AST_INDEX, AST_INPUT, AST_FLOAT, AST_TRUE, AST_FALSE,
    AST_FUNC_DEF, AST_FUNC_CALL, AST_RETURN, AST_NOT,
    AST_NEW_LIST, AST_NEW_DICT, AST_APPEND, AST_LEN // 新增 AST 型別
} ASTType;

typedef struct ASTNode {
    ASTType type; TokenType op; char name[256]; int value; double f_val;
    struct ASTNode *left, *right, *true_branch, *false_branch;
    struct ASTNode *cond, *step, *body, *next;
} ASTNode;

// 3. 記憶體與狀態結構
typedef struct { char name[256]; char fields[20][256]; int field_count; } StructDef;
typedef struct { char name[256]; ASTNode *params; ASTNode *body; } FuncDef;
typedef struct { char name[256]; int addr; } Symbol;
typedef struct { Value items[100]; int count; } ListObj; // 列表結構
typedef struct { char keys[100][256]; Value values[100]; int count; } DictObj; // 字典結構

// 4. 全域變數
extern char *src_code; extern int src_pos; extern Token current_token;
extern Value memory[MEM_SIZE]; extern int heap_ptr;
extern StructDef struct_table[50]; extern int struct_count;
extern FuncDef func_table[50]; extern int func_count;
extern ListObj list_pool[100]; extern int list_count; // 列表池
extern DictObj dict_pool[100]; extern int dict_count; // 字典池
extern Symbol sym_stack[20][100]; extern int sym_count[20]; extern int call_depth;
extern Value ret_val; extern int is_returning;

// 5. 模組函式介面
void advance_token(); void eat(TokenType type);
ASTNode* create_node(ASTType type);
ASTNode* parse_statement(); ASTNode* parse_block();
int alloc_mem(int size); int get_sym_addr(const char *name); int get_lvalue(ASTNode *node);
void dict_set(int dict_id, const char *key, Value val);
Value dict_get(int dict_id, const char *key);
void execute(ASTNode *stmt); Value eval(ASTNode *node); int is_truthy(Value v);

#endif