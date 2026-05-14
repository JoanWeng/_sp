#ifndef IO_H
#define IO_H

int my_strlen(const char *str);
void my_print_str(const char *str);
void my_print_int(int num);
void my_print_float(double f);
void my_print_newline();
void my_read_str(char *buf, int max_len);

// 🚀 新增：作業系統檔案與中斷介面
int my_open(const char *pathname);
long my_lseek(int fd, long offset, int whence);
long my_read(int fd, void *buf, unsigned long count);
void my_close(int fd);
void my_exit(int status);
void my_error(const char *msg, const char *arg); // 統一的錯誤報警器

#endif