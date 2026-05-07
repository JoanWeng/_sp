#include "emolang.h"

ASTNode* create_node(ASTType type) {
    ASTNode *node = (ASTNode*)calloc(1, sizeof(ASTNode));
    node->type = type;
    return node;
}

ASTNode* parse_expression();

ASTNode* parse_primary() {
    ASTNode *node;
    if (current_token.type == TOK_LPAREN) {
        eat(TOK_LPAREN);
        node = parse_expression();
        eat(TOK_RPAREN);
        return node;
    }
    
    node = create_node(AST_NUM);
    if (current_token.type == TOK_NUM) {
        node->value = atoi(current_token.value); eat(TOK_NUM);
    } else if (current_token.type == TOK_FLOAT_NUM) {
        node->type = AST_FLOAT; node->f_val = atof(current_token.value); eat(TOK_FLOAT_NUM);
    } else if (current_token.type == TOK_TRUE) {
        node->type = AST_TRUE; eat(TOK_TRUE);
    } else if (current_token.type == TOK_FALSE) {
        node->type = AST_FALSE; eat(TOK_FALSE);
    } else if (current_token.type == TOK_STR) {
        node->type = AST_STR; strcpy(node->name, current_token.value); eat(TOK_STR);
    } else if (current_token.type == TOK_ID) {
        char id_name[256];
        strcpy(id_name, current_token.value);
        eat(TOK_ID);
        
        // 核心更新：如果變數後面緊接著 '('，這是一個函數呼叫！
        if (current_token.type == TOK_LPAREN) {
            eat(TOK_LPAREN);
            node->type = AST_FUNC_CALL;
            strcpy(node->name, id_name);
            ASTNode *head = NULL, *tail = NULL;
            
            // 解析傳入的參數列表
            while (current_token.type != TOK_RPAREN && current_token.type != TOK_EOF) {
                ASTNode *arg = parse_expression();
                if (!head) head = tail = arg; 
                else { tail->next = arg; tail = arg; }
                
                if (current_token.type == TOK_COMMA) eat(TOK_COMMA); // 吃掉逗號
            }
            eat(TOK_RPAREN);
            node->left = head;
            return node;
        } else {
            // 如果沒有括號，那它就只是一個普通的變數
            node->type = AST_VAR;
            strcpy(node->name, id_name);
        }
    } else {
        printf("解析表達式出錯\n"); exit(1);
    }
    return node;
}

ASTNode* parse_postfix() {
    ASTNode* node = parse_primary();
    while (current_token.type == TOK_DOT || current_token.type == TOK_INDEX) {
        if (current_token.type == TOK_DOT) {
            eat(TOK_DOT);
            ASTNode* new_node = create_node(AST_DOT);
            new_node->left = node;
            strcpy(new_node->name, current_token.value);
            eat(TOK_ID);
            node = new_node;
        } else if (current_token.type == TOK_INDEX) {
            eat(TOK_INDEX);
            ASTNode* new_node = create_node(AST_INDEX);
            new_node->left = node;
            new_node->right = parse_primary();
            node = new_node;
        }
    }
    return node;
}

ASTNode* parse_prefix() {
    if (current_token.type == TOK_INPUT) {
        eat(TOK_INPUT);
        return create_node(AST_INPUT);
    } else if (current_token.type == TOK_REF) {
        eat(TOK_REF);
        ASTNode *node = create_node(AST_REF); node->left = parse_prefix(); return node;
    } else if (current_token.type == TOK_DEREF) {
        eat(TOK_DEREF);
        ASTNode *node = create_node(AST_DEREF); node->left = parse_prefix(); return node;
    } else if (current_token.type == TOK_NEW) {
        eat(TOK_NEW);
        if (current_token.type == TOK_ARRAY) {
            eat(TOK_ARRAY);
            ASTNode *node = create_node(AST_ARRAY_ALLOC);
            node->left = parse_primary();
            return node;
        } else {
            ASTNode *node = create_node(AST_NEW);
            strcpy(node->name, current_token.value); eat(TOK_ID);
            return node;
        }
    }
    return parse_postfix();
}

ASTNode* parse_factor() {
    ASTNode *node = parse_prefix();
    while (current_token.type == TOK_MUL || current_token.type == TOK_DIV || current_token.type == TOK_MOD) {
        ASTNode *new_node = create_node(AST_BINOP); new_node->op = current_token.type;
        new_node->left = node; eat(current_token.type); new_node->right = parse_prefix();
        node = new_node;
    }
    return node;
}

ASTNode* parse_addition() {
    ASTNode *node = parse_factor();
    while (current_token.type == TOK_PLUS || current_token.type == TOK_MINUS) {
        ASTNode *new_node = create_node(AST_BINOP); new_node->op = current_token.type;
        new_node->left = node; eat(current_token.type); new_node->right = parse_factor();
        node = new_node;
    }
    return node;
}

ASTNode* parse_expression() {
    ASTNode *node = parse_addition();
    if (current_token.type == TOK_EQ || current_token.type == TOK_GT || current_token.type == TOK_LT) {
        ASTNode *new_node = create_node(AST_BINOP); new_node->op = current_token.type;
        new_node->left = node; eat(current_token.type); new_node->right = parse_addition();
        node = new_node;
    }
    return node;
}

ASTNode* parse_block() {
    eat(TOK_LBRACE);
    ASTNode *head = NULL, *tail = NULL;
    while (current_token.type != TOK_RBRACE && current_token.type != TOK_EOF) {
        ASTNode *stmt = parse_statement();
        if (!head) head = tail = stmt; else { tail->next = stmt; tail = stmt; }
    }
    eat(TOK_RBRACE);
    return head;
}

ASTNode* parse_statement() {
    // 1. 定義函數 (🛠️ 函數名(參數) 👇 ... 👆)
    if (current_token.type == TOK_FUNC) {
        eat(TOK_FUNC);
        ASTNode *node = create_node(AST_FUNC_DEF);
        strcpy(node->name, current_token.value); eat(TOK_ID);
        eat(TOK_LPAREN);
        ASTNode *head = NULL, *tail = NULL;
        while (current_token.type != TOK_RPAREN && current_token.type != TOK_EOF) {
            ASTNode *p = create_node(AST_VAR); 
            strcpy(p->name, current_token.value); eat(TOK_ID); 
            if (!head) head = tail = p; else { tail->next = p; tail = p; }
            if (current_token.type == TOK_COMMA) eat(TOK_COMMA);
        }
        eat(TOK_RPAREN);
        node->left = head;
        node->body = parse_block();
        return node;
    }
    // 2. 函數回傳 (🔙 回傳值)
    else if (current_token.type == TOK_RETURN) {
        eat(TOK_RETURN);
        ASTNode *node = create_node(AST_RETURN);
        node->left = parse_expression();
        return node;
    }
    // 3. 變數宣告
    else if (current_token.type == TOK_LET) {
        eat(TOK_LET);
        ASTNode *node = create_node(AST_LET); strcpy(node->name, current_token.value); eat(TOK_ID);
        if (current_token.type == TOK_ASSIGN) { eat(TOK_ASSIGN); node->left = parse_expression(); }
        return node;
    } 
    // 4. 輸出
    else if (current_token.type == TOK_PRINT) {
        eat(TOK_PRINT); ASTNode *node = create_node(AST_PRINT); node->left = parse_expression(); return node;
    } 
    // 5. If / Else If / Else
    else if (current_token.type == TOK_IF) {
        eat(TOK_IF); ASTNode *node = create_node(AST_IF);
        node->left = parse_expression(); node->true_branch = parse_block();
        if (current_token.type == TOK_ELSE) { 
            eat(TOK_ELSE); 
            if (current_token.type == TOK_IF) node->false_branch = parse_statement();
            else node->false_branch = parse_block();
        }
        return node;
    } 
    // 6. While
    else if (current_token.type == TOK_WHILE) {
        eat(TOK_WHILE); ASTNode *node = create_node(AST_WHILE);
        node->left = parse_expression(); node->true_branch = parse_block();
        return node;
    } 
    // 7. For
    else if (current_token.type == TOK_FOR) {
        eat(TOK_FOR); ASTNode *node = create_node(AST_FOR);
        node->left = parse_statement(); eat(TOK_SEP); node->cond = parse_expression(); eat(TOK_SEP);
        node->step = parse_statement(); node->body = parse_block();
        return node;
    } 
    // 8. 結構體
    else if (current_token.type == TOK_STRUCT) {
        eat(TOK_STRUCT); ASTNode *node = create_node(AST_STRUCT_DEF);
        strcpy(node->name, current_token.value); eat(TOK_ID); node->body = parse_block();
        return node;
    }
    
    // 9. 一般運算式或賦值
    ASTNode *expr = parse_expression();
    if (current_token.type == TOK_ASSIGN) {
        eat(TOK_ASSIGN); ASTNode *node = create_node(AST_ASSIGN);
        node->left = expr; node->right = parse_expression(); return node;
    }
    return expr;
}