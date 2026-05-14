#include "../include/emolang.h"

// 直接在編譯期分配 1MB 的記憶體空間放源碼！
char src_buffer[1024 * 1024]; 
char *src_code = src_buffer;
int src_pos = 0;
Token current_token;

int main(int argc, char **argv) {
    if (argc < 2) {
        my_print_str("用法: ./emolang <filename.emo>\n");
        return 1;
    }

    // 呼叫 OS 的 open
    int fd = my_open(argv[1]);
    if (fd < 0) {
        my_print_str("❌ 找不到檔案或無法開啟\n");
        return 1;
    }

    // 計算檔案長度 (lseek 到檔案尾端再回去)
    long fsize = my_lseek(fd, 0, 2); // 2 = SEEK_END
    my_lseek(fd, 0, 0);              // 0 = SEEK_SET
    
    // 讀取進 1MB 的巨大陣列中
    my_read(fd, src_buffer, fsize);
    src_buffer[fsize] = '\0';
    my_close(fd);

    // 啟動編譯與執行
    advance_token();
    ASTNode *program = NULL, *tail = NULL;
    
    while (current_token.type != TOK_EOF) {
        ASTNode *stmt = parse_statement();
        if (!program) program = tail = stmt;
        else { tail->next = stmt; tail = stmt; }
    }

    execute(program);
    return 0;
}