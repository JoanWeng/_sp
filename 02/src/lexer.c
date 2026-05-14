#include "emolang.h"


// 包含所有 34 個 Emoji 的完整關鍵字表
const char *emoji_keywords[] = {
    "📦", "🔢", "🎈", "📝", "🚦", "🟰", "🤔", "🤷", "🔁", "👇", 
    "👆", "📢", "➕", "➖", "✖️", "➗", "✂️", "🤝", "📈", "📉", 
    "🎡", "🚧", "🏗️", "🆕", "➡️", "📍", "🎯", "📚", "📌", "📥", 
    "🟢", "🔴", "🛠️", "🔙", "🔗", "🔀", "🙅",
    "📋", "📖", "🛒", "📏"
};
// 對應的 34 個 Token
TokenType emoji_tokens[] = {
    TOK_LET, TOK_LET, TOK_LET, TOK_LET, TOK_LET,
    TOK_ASSIGN, TOK_IF, TOK_ELSE, TOK_WHILE, TOK_LBRACE, TOK_RBRACE, TOK_PRINT, TOK_PLUS, TOK_MINUS, TOK_MUL, 
    TOK_DIV, TOK_MOD, TOK_EQ, TOK_GT, TOK_LT, TOK_FOR, TOK_SEP, TOK_STRUCT, TOK_NEW, TOK_DOT, 
    TOK_REF, TOK_DEREF, TOK_ARRAY, TOK_INDEX, TOK_INPUT, TOK_TRUE, TOK_FALSE, TOK_FUNC, TOK_RETURN,
    TOK_AND, TOK_OR, TOK_NOT,
    TOK_LIST, TOK_DICT, TOK_APPEND, TOK_LEN
};

int match_keyword(const char *p) {
    for (int i = 0; i < 41; i++) { 
        int len = strlen(emoji_keywords[i]);
        if (strncmp(p, emoji_keywords[i], len) == 0) return i;
    }
    return -1;
}

void advance_token() {
    // 略過空白字元
    while (isspace(src_code[src_pos])) src_pos++;
    
    // 檢查是否結束
    if (src_code[src_pos] == '\0') { current_token.type = TOK_EOF; return; }
    
    // 標點符號判斷 (支援括號與函數參數的逗號)
    if (src_code[src_pos] == '(') { current_token.type = TOK_LPAREN; strcpy(current_token.value, "("); src_pos++; return; }
    if (src_code[src_pos] == ')') { current_token.type = TOK_RPAREN; strcpy(current_token.value, ")"); src_pos++; return; }
    if (src_code[src_pos] == ',') { current_token.type = TOK_COMMA; strcpy(current_token.value, ","); src_pos++; return; }
    
    // 解析字串
    if (src_code[src_pos] == '"') {
        src_pos++; int i = 0;
        while (src_code[src_pos] != '"' && src_code[src_pos] != '\0' && i < 255) {
            current_token.value[i++] = src_code[src_pos++];
        }
        current_token.value[i] = '\0';
        if (src_code[src_pos] == '"') src_pos++;
        current_token.type = TOK_STR; return;
    }
    
    // 解析數字與小數
    if (isdigit(src_code[src_pos])) {
        int i = 0, is_float = 0;
        while (isdigit(src_code[src_pos]) || src_code[src_pos] == '.') {
            if (src_code[src_pos] == '.') is_float = 1;
            current_token.value[i++] = src_code[src_pos++];
        }
        current_token.value[i] = '\0';
        current_token.type = is_float ? TOK_FLOAT_NUM : TOK_NUM; return;
    }
    
    // 解析 Emoji 關鍵字
    int kw_idx = match_keyword(&src_code[src_pos]);
    if (kw_idx != -1) {
        current_token.type = emoji_tokens[kw_idx];
        strcpy(current_token.value, emoji_keywords[kw_idx]);
        src_pos += strlen(emoji_keywords[kw_idx]); return;
    }
    
    // 解析普通變數名稱
    int i = 0;
    while (src_code[src_pos] != '\0' && !isspace(src_code[src_pos]) && 
           match_keyword(&src_code[src_pos]) == -1 && src_code[src_pos] != '"' &&
           src_code[src_pos] != '(' && src_code[src_pos] != ')' && src_code[src_pos] != ',') {
        current_token.value[i++] = src_code[src_pos++];
    }
    current_token.value[i] = '\0';
    current_token.type = TOK_ID;
}

void eat(TokenType type) {
    if (current_token.type == type) advance_token();
    else { my_error("語法錯誤: 遇到未預期的 Token", current_token.value); }
}