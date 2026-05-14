#include "../include/emolang.h"

#define MAX_AST_NODES 50000
ASTNode ast_pool[MAX_AST_NODES];
int ast_node_count = 0;

ASTNode* create_node(ASTType type) {
    if (ast_node_count >= MAX_AST_NODES) {
        my_error("AST 節點數量超出上限！請優化程式碼", NULL);
    }
    ASTNode *node = &ast_pool[ast_node_count++];
    
    // 手動清空記憶體 (取代 calloc)
    char *ptr = (char*)node;
    for(int i = 0; i < sizeof(ASTNode); i++) ptr[i] = 0;
    
    node->type = type;
    return node;
}