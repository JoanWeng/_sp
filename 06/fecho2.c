#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define SMAX 128

int main() {
    int fda = open("a.txt", O_RDWR);
    int fdb = open("b.txt", O_CREAT | O_RDWR, 0644);
    dup2(fda, 0);
    dup2(fdb, 1);
    char line[SMAX];
    fgets(line, SMAX, stdin);
    fputs(line, stdout);
}
