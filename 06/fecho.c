#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define SMAX 128

int main() {
    close(0);
    close(1);
    int a = open("a.txt", O_RDWR);
    int b = open("b.txt", O_CREAT | O_RDWR, 0644);
    char line[SMAX];
    fgets(line, SMAX, stdin);
    fputs(line, stdout);
    printf("a=%d, b=%d (should be 0, 1)\n", a, b);
}
