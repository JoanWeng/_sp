#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

#define BUFFER_SIZE 5
#define ITEMS 10

int buffer[BUFFER_SIZE];
int in = 0, out = 0;
int count = 0;

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cond_full = PTHREAD_COND_INITIALIZER;
pthread_cond_t cond_empty = PTHREAD_COND_INITIALIZER;

void put(int item) {
    buffer[in] = item;
    in = (in + 1) % BUFFER_SIZE;
    count++;
}

int get() {
    int item = buffer[out];
    out = (out + 1) % BUFFER_SIZE;
    count--;
    return item;
}

void* producer(void* arg) {
    int id = *(int*)arg;
    for (int i = 0; i < ITEMS; i++) {
        pthread_mutex_lock(&mutex);
        while (count == BUFFER_SIZE)
            pthread_cond_wait(&cond_full, &mutex);
        put(i);
        printf("P%d -> %d (count=%d)\n", id, i, count);
        pthread_cond_signal(&cond_empty);
        pthread_mutex_unlock(&mutex);
        usleep(rand() % 100000);
    }
    return NULL;
}

void* consumer(void* arg) {
    int id = *(int*)arg;
    for (int i = 0; i < ITEMS; i++) {
        pthread_mutex_lock(&mutex);
        while (count == 0)
            pthread_cond_wait(&cond_empty, &mutex);
        int item = get();
        printf("      C%d <- %d (count=%d)\n", id, item, count);
        pthread_cond_signal(&cond_full);
        pthread_mutex_unlock(&mutex);
        usleep(rand() % 150000);
    }
    return NULL;
}

int main() {
    pthread_t producers[2], consumers[2];
    int ids[4] = {0, 1, 0, 1};

    for (int i = 0; i < 2; i++)
        pthread_create(&producers[i], NULL, producer, &ids[i]);
    for (int i = 0; i < 2; i++)
        pthread_create(&consumers[i], NULL, consumer, &ids[i + 2]);

    for (int i = 0; i < 2; i++) pthread_join(producers[i], NULL);
    for (int i = 0; i < 2; i++) pthread_join(consumers[i], NULL);

    pthread_mutex_destroy(&mutex);
    pthread_cond_destroy(&cond_full);
    pthread_cond_destroy(&cond_empty);
    return 0;
}
