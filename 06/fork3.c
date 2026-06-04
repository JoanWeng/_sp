#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

int main() {
    int m = 100;
    printf("%-5d : before fork, m=%d\n", getpid(), m);
    int n = fork();
    if (n > 0) {
        m += 50;
        printf("%-5d : parent, m=%d n=%d\n", getpid(), m, n);
    } else {
        m += 10;
        printf("%-5d : child,  m=%d n=%d\n", getpid(), m, n);
    }
}
