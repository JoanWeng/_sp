#include "../include/utils.h"

// 1. 字串長度 (計算有幾個字元，直到遇到 \0)
int my_strlen(const char *str) {
    int len = 0;
    while (str[len] != '\0') len++;
    return len;
}

// 2. 字串比對 (完全相等回傳 0)
int my_strcmp(const char *s1, const char *s2) {
    while (*s1 && (*s1 == *s2)) { s1++; s2++; }
    return *(const unsigned char*)s1 - *(const unsigned char*)s2;
}

// 3. 長度限制的字串比對
int my_strncmp(const char *s1, const char *s2, unsigned long n) {
    if (n == 0) return 0;
    while (n-- > 0 && *s1 && *s1 == *s2) {
        if (n == 0) return 0;
        s1++; s2++;
    }
    return *(const unsigned char*)s1 - *(const unsigned char*)s2;
}

// 4. 字串複製
char *my_strcpy(char *dest, const char *src) {
    char *d = dest;
    while ((*d++ = *src++)); // 經典的 C 語言極簡寫法
    return dest;
}

// 5. 長度限制的字串複製
char *my_strncpy(char *dest, const char *src, unsigned long n) {
    char *d = dest;
    while (n > 0 && *src) { *d++ = *src++; n--; }
    while (n > 0) { *d++ = '\0'; n--; } // 補齊 \0
    return dest;
}

// 6. 字串串接 (把 src 黏到 dest 後面)
char *my_strncat(char *dest, const char *src, unsigned long n) {
    char *d = dest;
    while (*d) d++; // 走到 dest 的尾巴
    while (n-- > 0 && *src) *d++ = *src++;
    *d = '\0';
    return dest;
}

// 7. 尋找字元是否存在字串中
char *my_strchr(const char *str, int c) {
    while (*str) {
        if (*str == (char)c) return (char *)str;
        str++;
    }
    if (c == '\0') return (char *)str;
    return NULL;
}

// ==========================================
// 字元判斷 (CType)
// ==========================================
int my_isdigit(char c) { return c >= '0' && c <= '9'; }
int my_isspace(char c) { return c == ' ' || c == '\t' || c == '\n' || c == '\r'; }

// ==========================================
// 字串轉數字 (Stdlib)
// ==========================================
// 將字串 "123" 轉為整數 123
int my_atoi(const char *str) {
    int res = 0; int sign = 1; int i = 0;
    if (str[0] == '-') { sign = -1; i++; }
    for (; str[i] != '\0'; ++i) {
        if (!my_isdigit(str[i])) break;
        res = res * 10 + (str[i] - '0'); // ASCII 的 '0' 是 48，減去它就能得到真實數字
    }
    return sign * res;
}

// 將字串 "3.14" 轉為浮點數 3.14
double my_atof(const char *str) {
    double res = 0.0; double fraction = 1.0; 
    int sign = 1; int i = 0; int has_dot = 0;
    if (str[0] == '-') { sign = -1; i++; }
    for (; str[i] != '\0'; ++i) {
        if (str[i] == '.') { has_dot = 1; continue; }
        if (!my_isdigit(str[i])) break;
        if (!has_dot) {
            res = res * 10.0 + (str[i] - '0');
        } else {
            fraction *= 0.1;
            res += (str[i] - '0') * fraction;
        }
    }
    return sign * res;
}

void my_itoa(int num, char *buf) {
    int i = 0, is_neg = 0;
    if (num == 0) { buf[0] = '0'; buf[1] = '\0'; return; }
    if (num < 0) { is_neg = 1; num = -num; }
    while (num > 0) { buf[i++] = '0' + (num % 10); num /= 10; }
    if (is_neg) buf[i++] = '-';
    buf[i] = '\0';
    // 將字串反轉
    for (int j = 0; j < i / 2; j++) { char t = buf[j]; buf[j] = buf[i - 1 - j]; buf[i - 1 - j] = t; }
}

void my_ftoa(double f, char *buf) {
    if (f < 0) { *buf++ = '-'; f = -f; }
    int int_part = (int)f; double frac = f - int_part;
    my_itoa(int_part, buf);
    int len = my_strlen(buf);
    buf[len++] = '.';
    for (int i = 0; i < 4; i++) {
        frac *= 10; int d = (int)frac;
        buf[len++] = '0' + d; frac -= d;
    }
    buf[len] = '\0';
}