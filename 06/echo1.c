#include <stdio.h>
#include <unistd.h>

#define SMAX 128

int main() {
    char line[SMAX];
    int n = read(0, line, SMAX);
    line[n] = '\0';
    write(1, line, n);
    write(2, line, n);
}
