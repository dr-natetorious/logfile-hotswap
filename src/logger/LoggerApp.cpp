#include "LoggerApp.hpp"
#include <iostream>
#include <fstream>
#include <csignal>
#include <chrono>
#include <random>

// Global variables with better encapsulation in anonymous namespace
namespace {
    std::ofstream log_file;
    std::mutex file_mutex;
    std::atomic<bool> running{true};
    int sleep_ms = 1000; // Default value
    
    // Signal handler for CTRL+C
    void handle_sigint(int) {
        std::cout << "\nReceived SIGINT (Ctrl+C). Gracefully shutting down...\n";
        running = false;
    }
}

// Make global variables accessible to other files that need them
namespace GlobalState {
    extern std::ofstream& getLogFile() { return log_file; }
    extern std::mutex& getFileMutex() { return file_mutex; }
    extern bool isRunning() { return running; }
    extern int getSleepMs() { return sleep_ms; }
}

LoggerApp::LoggerApp(const std::string& logfile_path, int thread_count, int sleep_ms_value) {
    // Validate and store sleep_ms globally
    if (sleep_ms_value < 0) {
        throw std::invalid_argument("sleep_ms must be a non-negative integer");
    }
    sleep_ms = sleep_ms_value;
    
    // Open log file with proper error handling
    log_file.open(logfile_path, std::ios::app);
    if (!log_file) {
        throw std::runtime_error("Error opening log file: " + logfile_path);
    }
    
    // Set up signal handler
    std::signal(SIGINT, handle_sigint);
    
    // Initialize threads
    if (thread_count <= 0) {
        throw std::invalid_argument("thread_count must be a positive integer");
    }
    
    // Store thread-related info
    thread_count_ = thread_count;
}

LoggerApp::~LoggerApp() {
    // Join any remaining threads and close file in destructor
    joinAllThreads();
    if (log_file.is_open()) {
        log_file.close();
    }
}

void LoggerApp::run() {
    std::cout << "Creating " << thread_count_ << " threads...\n";
    
    // Create and start threads using modern C++ random
    std::mt19937 gen{std::random_device{}()};
    std::uniform_int_distribution<> jitter_dist(0, 1000);
    
    for (int i = 0; i < thread_count_; ++i) {
        // Generate jitter with both random and deterministic components
        int jitter_ms = jitter_dist(gen) + (i * 37) % 200;
        
        // Create unique thread object with its parameters
        auto logger = std::make_unique<LoggerThread>(i, jitter_ms);
        
        // Launch thread with the functor
        threads_.emplace_back(std::thread(std::ref(*logger)));
        
        // Store the logger object so it lives as long as the thread
        loggers_.push_back(std::move(logger));
        
        std::cout << "Thread " << i << " started!\n";
    }

    std::cout << "\nAll threads are running. Each thread writes to the log file every " 
              << sleep_ms << " ms.\n";
    std::cout << "Press Ctrl+C to gracefully terminate the process.\n";

    // Wait for CTRL+C
    while (running) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    
    joinAllThreads();
    std::cout << "Application has terminated gracefully.\n";
}

void LoggerApp::joinAllThreads() {
    if (!threads_.empty()) {
        std::cout << "Waiting for all threads to finish...\n";
        for (size_t i = 0; i < threads_.size(); ++i) {
            if (threads_[i].joinable()) {
                threads_[i].join();
                std::cout << "Thread " << i << " has terminated.\n";
            }
        }
        threads_.clear();
        loggers_.clear();
    }
}
