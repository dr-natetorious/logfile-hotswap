#pragma once

#include <atomic>
#include <mutex>
#include <fstream>

// Forward declarations for globals accessed in ThreadLogger.cpp
namespace GlobalState {
    extern std::mutex& getFileMutex();
    extern std::ofstream& getLogFile();
    extern bool isRunning();
    extern int getSleepMs();
}

// Modern C++ class for thread management
class LoggerThread {
public:
    // Constructor initializes thread with ID and jitter
    LoggerThread(int id, int jitter_ms);
    
    // Thread function operator
    void operator()();
    
private:
    int thread_id_;
    int jitter_ms_;
    int counter_;
};