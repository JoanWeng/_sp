#include <stdio.h>
#include <pthread.h>

#define TIMES 100000

int balance = 100000;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void* deposit(void* arg) {
    for (int i = 0; i < TIMES; i++) {
        pthread_mutex_lock(&mutex);
        balance++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

void* withdraw(void* arg) {
    for (int i = 0; i < TIMES; i++) {
        pthread_mutex_lock(&mutex);
        balance--;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2;

    printf("Before: balance = %d\n", balance);

    // 不加上鎖的情況 — 註解掉來看 race condition
    // pthread_create(&t1, NULL, deposit_race, NULL);
    // pthread_create(&t2, NULL, withdraw_race, NULL);

    pthread_create(&t1, NULL, deposit, NULL);
    pthread_create(&t2, NULL, withdraw, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    printf("After:  balance = %d (expect %d)\n", balance, 100000);
    pthread_mutex_destroy(&mutex);
    return 0;
}
