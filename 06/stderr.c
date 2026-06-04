#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

int main() {
    int fdb = open("log.txt", O_APPEND | O_CREAT | O_RDWR, 0644);
    dup2(fdb, 2);
    fprintf(stdout, "Hello World! (to stdout)\n");
    fprintf(stderr, "Warning: xxx (to stderr)\n");
    fprintf(stderr, "Error: yyy (to stderr)\n");
}
