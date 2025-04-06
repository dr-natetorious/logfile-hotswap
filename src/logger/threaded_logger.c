#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <signal.h>
#include <time.h>
#include <stdbool.h>

// Global variables
FILE *log_file = NULL;
pthread_mutex_t file_mutex = PTHREAD_MUTEX_INITIALIZER;
bool running = true;
int sleep_ms = 1000; // Default value

// Structure to pass data to threads
typedef struct {
    int thread_id;
} thread_data_t;

// Signal handler for CTRL+C
void handle_sigint(int sig __attribute__((unused))){
    printf("\nReceived SIGINT (Ctrl+C). Gracefully shutting down...\n");
    running = false;
}

// Thread function
void *thread_function(void *arg) {
    thread_data_t *data = (thread_data_t *)arg;
    int counter = 0;
    char timestamp[64];
    time_t now;
    struct tm *tm_info;

    while (running) {
        // Get current time
        time(&now);
        tm_info = localtime(&now);
        strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", tm_info);

        // Log message with mutex protection to avoid file corruption
        pthread_mutex_lock(&file_mutex);
        fprintf(log_file, "Thread %d: [%s] Has counter %d\n", data->thread_id, timestamp, counter++);
        fflush(log_file); // Ensure it's written immediately
        pthread_mutex_unlock(&file_mutex);

        // Sleep for the specified milliseconds
        usleep(sleep_ms * 1000); // Convert ms to microseconds
    }

    pthread_mutex_lock(&file_mutex);
    fprintf(log_file, "Thread %d: Shutting down gracefully.\n", data->thread_id);
    fflush(log_file);
    pthread_mutex_unlock(&file_mutex);

    free(data); // Free the allocated thread data
    return NULL;
}

void print_usage(const char *program_name) {
    printf("Usage: %s <logfile_path> <thread_count> <sleep_ms>\n", program_name);
    printf("  logfile_path: Path to the log file\n");
    printf("  thread_count: Number of threads to create\n");
    printf("  sleep_ms: Milliseconds to sleep between log entries\n");
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        print_usage(argv[0]);
        return 1;
    }

    // Parse command line arguments
    const char *logfile_path = argv[1];
    int thread_count = atoi(argv[2]);
    sleep_ms = atoi(argv[3]);

    // Validate arguments
    if (thread_count <= 0) {
        fprintf(stderr, "Error: thread_count must be a positive integer\n");
        return 1;
    }

    if (sleep_ms < 0) {
        fprintf(stderr, "Error: sleep_ms must be a non-negative integer\n");
        return 1;
    }

    // Open log file
    log_file = fopen(logfile_path, "a");
    if (log_file == NULL) {
        perror("Error opening log file");
        return 1;
    }

    // Set up signal handler for CTRL+C
    signal(SIGINT, handle_sigint);

    // Create threads
    pthread_t threads[thread_count];
    printf("Creating %d threads...\n", thread_count);

    for (int i = 0; i < thread_count; i++) {
        thread_data_t *data = malloc(sizeof(thread_data_t));
        if (data == NULL) {
            perror("Failed to allocate memory for thread data");
            fclose(log_file);
            return 1;
        }
        
        data->thread_id = i;
        
        if (pthread_create(&threads[i], NULL, thread_function, data) != 0) {
            perror("Failed to create thread");
            free(data);
            fclose(log_file);
            return 1;
        }
        
        printf("Thread %d started!\n", i);
    }

    printf("\nAll threads are running. Each thread writes to the log file every %d ms.\n", sleep_ms);
    printf("Press Ctrl+C to gracefully terminate the process.\n");

    // Wait for CTRL+C
    while (running) {
        sleep(1);
    }

    // Join all threads
    printf("Waiting for all threads to finish...\n");
    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
        printf("Thread %d has terminated.\n", i);
    }

    // Clean up
    pthread_mutex_destroy(&file_mutex);
    fclose(log_file);
    printf("Application has terminated gracefully.\n");

    return 0;
}
