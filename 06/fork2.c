#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

int main() {
    printf("%-5d : before fork\n", getpid());
    int rfork = fork();
    printf("rfork=%d\n", rfork);
    if (rfork == 0) {
        printf("%-5d : I am child!\n", getpid());
    } else {
        printf("%-5d : I am parent! (child pid=%d)\n", getpid(), rfork);
    }
    printf("%-5d : finished\n", getpid());
}
