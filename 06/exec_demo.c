#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main() {
    char *args[] = {"ls", "-l", NULL};

    fflush(stdout);
    pid_t pid = fork();
    if (pid == 0) {
        printf("child(%d): about to exec 'ls -l'\n", getpid());
        execvp(args[0], args);
        perror("execvp failed");
        return 1;
    } else {
        printf("parent(%d): waiting for child(%d)...\n", getpid(), pid);
        wait(NULL);
        printf("parent: child finished.\n");
    }
}
