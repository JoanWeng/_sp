#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

int main() {
    fork();
    printf("%-5d : Hello world!\n", getpid());
}
