#include "LoggerThread.hpp"
#include <iostream>
#include <fstream>
#include <thread>
#include <chrono>
#include <format>
#include <random>

LoggerThread::LoggerThread(int id, int jitter_ms) 
    : thread_id_(id), jitter_ms_(jitter_ms), counter_(0) {}
    
void LoggerThread::operator()() {
    // Apply initial jitter to stagger thread starts
    std::this_thread::sleep_for(std::chrono::milliseconds(jitter_ms_));
    
    while (GlobalState::isRunning()) {
        // Get current time
        auto now = std::chrono::system_clock::now();
        auto time_t_now = std::chrono::system_clock::to_time_t(now);
        std::tm tm_info = *std::localtime(&time_t_now);
        
        // Format timestamp using C++20 std::format
        std::string timestamp = std::format("{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}",
            tm_info.tm_year + 1900, tm_info.tm_mon + 1, tm_info.tm_mday,
            tm_info.tm_hour, tm_info.tm_min, tm_info.tm_sec);

        // Log message with mutex protection
        {
            std::lock_guard<std::mutex> lock(GlobalState::getFileMutex());
            GlobalState::getLogFile() << "Thread " << thread_id_ << ": [" << timestamp 
                     << "] Has counter " << counter_++ << std::endl;
        }

        // Sleep with random jitter
        // Using proper C++ random number generation
        static thread_local std::mt19937 gen{std::random_device{}()};
        std::uniform_int_distribution<> dist(-25, 25);
        int actual_sleep = GlobalState::getSleepMs() + dist(gen);
        actual_sleep = std::max(10, actual_sleep);  // Ensure minimum sleep time
        std::this_thread::sleep_for(std::chrono::milliseconds(actual_sleep));
    }

    // Log thread shutdown
    {
        std::lock_guard<std::mutex> lock(GlobalState::getFileMutex());
        GlobalState::getLogFile() << "Thread " << thread_id_ << ": Shutting down gracefully." << std::endl;
    }
}