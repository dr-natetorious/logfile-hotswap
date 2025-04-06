#include <iostream>
#include <string>
#include <exception>
#include "LoggerApp.hpp"

void print_usage(const std::string& program_name) {
    std::cout << "Usage: " << program_name << " <logfile_path> <thread_count> <sleep_ms>\n";
    std::cout << "  logfile_path: Path to the log file\n";
    std::cout << "  thread_count: Number of threads to create\n";
    std::cout << "  sleep_ms: Milliseconds to sleep between log entries\n";
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        print_usage(argv[0]);
        return 1;
    }

    try {
        // Parse command line arguments
        std::string logfile_path = argv[1];
        int thread_count = std::stoi(argv[2]);
        int sleep_ms = std::stoi(argv[3]);
        
        // Run the application
        LoggerApp app(logfile_path, thread_count, sleep_ms);
        app.run();
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}