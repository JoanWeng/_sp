#include "../include/io.h"

// 宣告作業系統底層系統呼叫
extern long write(int fd, const void *buf, unsigned long count);
extern long read(int fd, void *buf, unsigned long count);
extern int open(const char *pathname, int flags);
extern long lseek(int fd, long offset, int whence);
extern int close(int fd);
extern void _exit(int status);

// ... (保留原本的 my_strlen 到 my_read_str 的實作) ...
void my_print_str(const char *str) { write(1, str, my_strlen(str)); }
void my_print_int(int num) {
    if (num == 0) { my_print_str("0"); return; }
    if (num < 0) { my_print_str("-"); num = -num; }
    char buf[32]; int i = 31; buf[i] = '\0';
    while (num > 0) { i--; buf[i] = '0' + (num % 10); num /= 10; }
    my_print_str(&buf[i]);
}
void my_print_float(double f) {
    if (f < 0) { my_print_str("-"); f = -f; }
    int int_part = (int)f; double frac_part = f - int_part;
    my_print_int(int_part); my_print_str(".");
    for (int i = 0; i < 4; i++) {
        frac_part *= 10; int digit = (int)frac_part; char c = '0' + digit;
        write(1, &c, 1); frac_part -= digit;
    }
}
void my_print_newline() { my_print_str("\n"); }
void my_read_str(char *buf, int max_len) {
    int i = 0; char c;
    while (i < max_len - 1) {
        long b = read(0, &c, 1);
        if (b <= 0 || c == '\n' || c == ' ' || c == '\r') { if (i > 0) break; else continue; }
        buf[i++] = c;
    }
    buf[i] = '\0';
}

// 🚀 新增：OS 檔案讀寫與程式中斷實作
int my_open(const char *pathname) { return open(pathname, 0); } // 0 = O_RDONLY
long my_lseek(int fd, long offset, int whence) { return lseek(fd, offset, whence); }
long my_read(int fd, void *buf, unsigned long count) { return read(fd, buf, count); }
void my_close(int fd) { close(fd); }
void my_exit(int status) { _exit(status); }

// 統一的崩潰處理器 (完全取代原本所有的 printf("...%s"); exit(1); )
void my_error(const char *msg, const char *arg) {
    my_print_str("\n❌ 致命錯誤: ");
    my_print_str(msg);
    if (arg) {
        my_print_str(" [");
        my_print_str(arg);
        my_print_str("]");
    }
    my_print_newline();
    my_exit(1);
}