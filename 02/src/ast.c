#include "emolang.h"

ASTNode* create_node(ASTType type) {
    ASTNode *node = (ASTNode*)calloc(1, sizeof(ASTNode));
    node->type = type;
    return node;
}