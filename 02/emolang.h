#ifndef EMOLANG_H
#define EMOLANG_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// 定義所有 Token
typedef enum {
    TOK_LET, TOK_ASSIGN, TOK_IF, TOK_ELSE, TOK_WHILE, TOK_FOR,
    TOK_LBRACE, TOK_RBRACE, TOK_SEP, TOK_PRINT,
    TOK_PLUS, TOK_MINUS, TOK_MUL, TOK_DIV, TOK_MOD,
    TOK_EQ, TOK_GT, TOK_LT,
    TOK_STRUCT, TOK_NEW, TOK_DOT, TOK_REF, TOK_DEREF,
    TOK_ARRAY, TOK_INDEX, TOK_INPUT, TOK_LPAREN, TOK_RPAREN, TOK_COMMA,
    TOK_NUM, TOK_FLOAT_NUM, TOK_TRUE, TOK_FALSE, TOK_STR, TOK_ID,
    TOK_FUNC, TOK_RETURN, TOK_AND, TOK_OR, TOK_NOT, TOK_EOF
} TokenType;

typedef struct { TokenType type; char value[256]; } Token;

typedef struct { int type; int i; double f; char s[256]; } Value;

extern char *src_code; extern int src_pos; extern Token current_token;
void advance_token(); void eat(TokenType type);

typedef enum {
    AST_LET, AST_ASSIGN, AST_IF, AST_WHILE, AST_FOR, AST_PRINT,
    AST_BLOCK, AST_BINOP, AST_NUM, AST_STR, AST_VAR,
    AST_STRUCT_DEF, AST_NEW, AST_DOT, AST_REF, AST_DEREF,
    AST_ARRAY_ALLOC, AST_INDEX, AST_INPUT, AST_FLOAT, AST_TRUE, AST_FALSE,
    AST_FUNC_DEF, AST_FUNC_CALL, AST_RETURN, AST_NOT
} ASTType;

typedef struct ASTNode {
    ASTType type; TokenType op; char name[256]; int value; double f_val;
    struct ASTNode *left, *right, *true_branch, *false_branch;
    struct ASTNode *cond, *step, *body, *next;
} ASTNode;

ASTNode* create_node(ASTType type); ASTNode* parse_statement(); ASTNode* parse_block();
void execute(ASTNode *stmt); Value eval(ASTNode *node);

#endif