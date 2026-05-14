#include "../include/io.h"

// 宣告作業系統的底層系統呼叫 (POSIX 標準)
extern long write(int fd, const void *buf, unsigned long count);
extern long read(int fd, void *buf, unsigned long count);

// 自製輸出字串
void my_print_str(const char *str) {
    write(1, str, my_strlen(str)); // 檔案代號 1 代表 stdout (螢幕)
}

// 自製輸出整數
void my_print_int(int num) {
    if (num == 0) { my_print_str("0"); return; }
    if (num < 0) { my_print_str("-"); num = -num; }
    
    char buf[32];
    int i = 31;
    buf[i] = '\0';
    
    while (num > 0) {
        i--;
        buf[i] = '0' + (num % 10);
        num /= 10;
    }
    my_print_str(&buf[i]);
}

// 自製輸出小數
void my_print_float(double f) {
    if (f < 0) { my_print_str("-"); f = -f; }
    
    int int_part = (int)f;
    double frac_part = f - int_part;
    
    my_print_int(int_part);
    my_print_str(".");
    
    for (int i = 0; i < 4; i++) {
        frac_part *= 10;
        int digit = (int)frac_part;
        char c = '0' + digit;
        write(1, &c, 1);
        frac_part -= digit;
    }
}

// 自製換行
void my_print_newline() {
    my_print_str("\n");
}

// 自製鍵盤輸入讀取
void my_read_str(char *buf, int max_len) {
    int i = 0;
    char c;
    while (i < max_len - 1) {
        long bytes_read = read(0, &c, 1); // 檔案代號 0 代表 stdin (鍵盤)
        if (bytes_read <= 0 || c == '\n' || c == ' ' || c == '\r') {
            if (i > 0) break;
            else continue;
        }
        buf[i++] = c;
    }
    buf[i] = '\0';
}