#include "emolang.h"

// 提前宣告
ASTNode* parse_expression();

// 1. 最基礎的值 (數字、字串、變數、函數呼叫、括號)
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
        
        // 變數後面接括號 -> 函數呼叫
        if (current_token.type == TOK_LPAREN) {
            eat(TOK_LPAREN);
            node->type = AST_FUNC_CALL;
            strcpy(node->name, id_name);
            ASTNode *head = NULL, *tail = NULL;
            
            while (current_token.type != TOK_RPAREN && current_token.type != TOK_EOF) {
                ASTNode *arg = parse_expression();
                if (!head) head = tail = arg; 
                else { tail->next = arg; tail = arg; }
                if (current_token.type == TOK_COMMA) eat(TOK_COMMA);
            }
            eat(TOK_RPAREN);
            node->left = head;
            return node;
        } else {
            node->type = AST_VAR;
            strcpy(node->name, id_name);
        }
    } else {
        my_error("解析表達式出錯，遇到未知的 Token", current_token.value);
    }
    return node;
}

// 2. 後綴操作 (結構體 . / 陣列與字典索引 📌)
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

// 3. 前綴操作 (長度 📏、輸入 📥、新建 🆕、指標 📍 🎯、反轉 🙅)
ASTNode* parse_prefix() {
    if (current_token.type == TOK_LEN) {
        eat(TOK_LEN); 
        ASTNode *node = create_node(AST_LEN); 
        node->left = parse_prefix(); 
        return node;
    } else if (current_token.type == TOK_INPUT) {
        eat(TOK_INPUT);
        return create_node(AST_INPUT);
    } else if (current_token.type == TOK_NOT) {
        eat(TOK_NOT);
        ASTNode *node = create_node(AST_NOT);
        node->left = parse_prefix();
        return node;
    } else if (current_token.type == TOK_REF) {
        eat(TOK_REF);
        ASTNode *node = create_node(AST_REF); 
        node->left = parse_prefix(); 
        return node;
    } else if (current_token.type == TOK_DEREF) {
        eat(TOK_DEREF);
        ASTNode *node = create_node(AST_DEREF); 
        node->left = parse_prefix(); 
        return node;
    } else if (current_token.type == TOK_NEW) {
        eat(TOK_NEW);
        if (current_token.type == TOK_LIST) {
            eat(TOK_LIST); return create_node(AST_NEW_LIST);
        } else if (current_token.type == TOK_DICT) {
            eat(TOK_DICT); return create_node(AST_NEW_DICT);
        } else if (current_token.type == TOK_ARRAY) {
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

// 4. 乘除餘 (✖️, ➗, ✂️)
ASTNode* parse_factor() {
    ASTNode *node = parse_prefix();
    while (current_token.type == TOK_MUL || current_token.type == TOK_DIV || current_token.type == TOK_MOD) {
        ASTNode *new_node = create_node(AST_BINOP); 
        new_node->op = current_token.type;
        new_node->left = node; 
        eat(current_token.type); 
        new_node->right = parse_prefix();
        node = new_node;
    }
    return node;
}

// 5. 加減法 (➕, ➖)
ASTNode* parse_addition() {
    ASTNode *node = parse_factor();
    while (current_token.type == TOK_PLUS || current_token.type == TOK_MINUS) {
        ASTNode *new_node = create_node(AST_BINOP); 
        new_node->op = current_token.type;
        new_node->left = node; 
        eat(current_token.type); 
        new_node->right = parse_factor();
        node = new_node;
    }
    return node;
}

// 6. 比較大小 (🤝, 📈, 📉)
ASTNode* parse_comparison() {
    ASTNode *node = parse_addition();
    if (current_token.type == TOK_EQ || current_token.type == TOK_GT || current_token.type == TOK_LT) {
        ASTNode *new_node = create_node(AST_BINOP); 
        new_node->op = current_token.type;
        new_node->left = node; 
        eat(current_token.type); 
        new_node->right = parse_addition();
        node = new_node;
    }
    return node;
}

// 7. 邏輯 AND (🔗)
ASTNode* parse_logical_and() {
    ASTNode *node = parse_comparison();
    while (current_token.type == TOK_AND) {
        ASTNode *new_node = create_node(AST_BINOP); 
        new_node->op = current_token.type;
        new_node->left = node; 
        eat(current_token.type); 
        new_node->right = parse_comparison();
        node = new_node;
    }
    return node;
}

// 8. 邏輯 OR (🔀) -> 這是最終的 Expression
ASTNode* parse_expression() {
    ASTNode *node = parse_logical_and();
    while (current_token.type == TOK_OR) {
        ASTNode *new_node = create_node(AST_BINOP); 
        new_node->op = current_token.type;
        new_node->left = node; 
        eat(current_token.type); 
        new_node->right = parse_logical_and();
        node = new_node;
    }
    return node;
}

// 區塊解析 👇 ... 👆
ASTNode* parse_block() {
    eat(TOK_LBRACE);
    ASTNode *head = NULL, *tail = NULL;
    while (current_token.type != TOK_RBRACE && current_token.type != TOK_EOF) {
        ASTNode *stmt = parse_statement();
        if (!head) head = tail = stmt; 
        else { tail->next = stmt; tail = stmt; }
    }
    eat(TOK_RBRACE);
    return head;
}

// 解析每一行指令 (Statement)
ASTNode* parse_statement() {
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
    else if (current_token.type == TOK_RETURN) {
        eat(TOK_RETURN);
        ASTNode *node = create_node(AST_RETURN);
        node->left = parse_expression();
        return node;
    }
    else if (current_token.type == TOK_LET) {
        eat(TOK_LET);
        ASTNode *node = create_node(AST_LET); 
        strcpy(node->name, current_token.value); eat(TOK_ID);
        if (current_token.type == TOK_ASSIGN) { 
            eat(TOK_ASSIGN); 
            node->left = parse_expression(); 
        }
        return node;
    } 
    else if (current_token.type == TOK_PRINT) {
        eat(TOK_PRINT); 
        ASTNode *node = create_node(AST_PRINT); 
        node->left = parse_expression(); 
        return node;
    } 
    else if (current_token.type == TOK_IF) {
        eat(TOK_IF); 
        ASTNode *node = create_node(AST_IF);
        node->left = parse_expression(); 
        node->true_branch = parse_block();
        if (current_token.type == TOK_ELSE) { 
            eat(TOK_ELSE); 
            if (current_token.type == TOK_IF) node->false_branch = parse_statement();
            else node->false_branch = parse_block();
        }
        return node;
    } 
    else if (current_token.type == TOK_WHILE) {
        eat(TOK_WHILE); 
        ASTNode *node = create_node(AST_WHILE);
        node->left = parse_expression(); 
        node->true_branch = parse_block();
        return node;
    } 
    else if (current_token.type == TOK_FOR) {
        eat(TOK_FOR); 
        ASTNode *node = create_node(AST_FOR);
        node->left = parse_statement(); eat(TOK_SEP); 
        node->cond = parse_expression(); eat(TOK_SEP);
        node->step = parse_statement(); 
        node->body = parse_block();
        return node;
    } 
    else if (current_token.type == TOK_STRUCT) {
        eat(TOK_STRUCT); 
        ASTNode *node = create_node(AST_STRUCT_DEF);
        strcpy(node->name, current_token.value); eat(TOK_ID); 
        node->body = parse_block();
        return node;
    }
    
    // 處理普通運算、賦值 (🟰)、或追加清單 (🛒)
    ASTNode *expr = parse_expression();
    if (current_token.type == TOK_ASSIGN) {
        eat(TOK_ASSIGN); 
        ASTNode *node = create_node(AST_ASSIGN);
        node->left = expr; 
        node->right = parse_expression(); 
        return node;
    } 
    else if (current_token.type == TOK_APPEND) {
        eat(TOK_APPEND); 
        ASTNode *node = create_node(AST_APPEND);
        node->left = expr; 
        node->right = parse_expression(); 
        return node;
    }
    
    return expr;
}