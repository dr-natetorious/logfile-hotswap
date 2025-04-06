#pragma once

#include <string>
#include <vector>
#include <thread>
#include <memory>
#include "ThreadLogger.hpp"  // Updated to match your filename

// Logger application class
class LoggerApp {
public:
    // Constructor takes log file path, number of threads, and sleep duration
    LoggerApp(const std::string& logfile_path, int thread_count, int sleep_ms_value);
    
    // Destructor ensures all resources are properly released
    ~LoggerApp();
    
    // Non-copyable
    LoggerApp(const LoggerApp&) = delete;
    LoggerApp& operator=(const LoggerApp&) = delete;
    
    // Main method to run the application
    void run();
    
private:
    // Helper method to join all threads
    void joinAllThreads();

    // Member variables
    int thread_count_;
    std::vector<std::thread> threads_;
    std::vector<std::unique_ptr<LoggerThread>> loggers_;
};