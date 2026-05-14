#ifndef UTILS_H
#define UTILS_H

// 如果環境中沒有定義 NULL，我們自己定義它 (記憶體位址 0)
#ifndef NULL
#define NULL ((void*)0)
#endif

// 🚀 宣告我們徒手刻的基礎函式
int my_strlen(const char *str);
int my_strcmp(const char *s1, const char *s2);
int my_strncmp(const char *s1, const char *s2, unsigned long n);
char *my_strcpy(char *dest, const char *src);
char *my_strncpy(char *dest, const char *src, unsigned long n);
char *my_strncat(char *dest, const char *src, unsigned long n);
char *my_strchr(const char *str, int c);

int my_isdigit(char c);
int my_isspace(char c);

int my_atoi(const char *str);
double my_atof(const char *str);

// 🪄 巨集魔法：讓舊的程式碼自動轉向呼叫我們的新函式！
#define strlen my_strlen
#define strcmp my_strcmp
#define strncmp my_strncmp
#define strcpy my_strcpy
#define strncpy my_strncpy
#define strncat my_strncat
#define strchr my_strchr
#define isdigit my_isdigit
#define isspace my_isspace
#define atoi my_atoi
#define atof my_atof

#endif