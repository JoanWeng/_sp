#include "emolang.h"

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("用法: %s <filename.emo>\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    src_code = (char*)malloc(fsize + 1);
    fread(src_code, 1, fsize, f);
    src_code[fsize] = '\0';
    fclose(f);

    advance_token();
    ASTNode *program = NULL, *tail = NULL;
    
    while (current_token.type != TOK_EOF) {
        ASTNode *stmt = parse_statement();
        if (!program) program = tail = stmt;
        else { tail->next = stmt; tail = stmt; }
    }

    execute(program);
    free(src_code);
    return 0;
}