#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

#define N 5
#define LEFT (i + N - 1) % N
#define RIGHT (i + 1) % N

pthread_mutex_t forks[N];

void think(int i) {
    printf("Philosopher %d is thinking...\n", i);
    usleep(rand() % 500000);
}

void eat(int i) {
    printf("Philosopher %d is eating...\n", i);
    usleep(rand() % 500000);
}

void pickup_forks_ordered(int i) {
    int first = i;
    int second = RIGHT;
    if (first > second) {
        first = second;
        second = i;
    }
    pthread_mutex_lock(&forks[first]);
    pthread_mutex_lock(&forks[second]);
}

void putdown_forks(int i) {
    pthread_mutex_unlock(&forks[i]);
    pthread_mutex_unlock(&forks[RIGHT]);
}

void* philosopher(void* arg) {
    int i = *(int*)arg;
    while (1) {
        think(i);
        pickup_forks_ordered(i);
        eat(i);
        putdown_forks(i);
    }
    return NULL;
}

int main() {
    setbuf(stdout, NULL);
    pthread_t phils[N];
    int ids[N];

    for (int i = 0; i < N; i++)
        pthread_mutex_init(&forks[i], NULL);

    for (int i = 0; i < N; i++) {
        ids[i] = i;
        pthread_create(&phils[i], NULL, philosopher, &ids[i]);
    }

    for (int i = 0; i < N; i++)
        pthread_join(phils[i], NULL);

    for (int i = 0; i < N; i++)
        pthread_mutex_destroy(&forks[i]);

    return 0;
}
