# Logfile Hotswap Toolkit

A toolkit for building and managing logging applications with live log file redirection capabilities.

## Components

This project consists of two main components:

1. **Logger**: A multi-threaded C application that demonstrates continuous logging to files
2. **Hotswap**: A Python utility that allows redirecting file descriptors in a running process

## Requirements

### Logger Requirements

- GCC compiler
- Make build system

### Hotswap Requirements

- Python 3.12+
- PyInstaller (automatically installed by the build system)
- GDB (for file descriptor redirection)

## Project Structure

```
logfile-hotswap/
├── bin/                 # Compiled binaries output directory
├── src/                 # Source code
│   ├── logger/          # C logger application
│   │   ├── Makefile     # Build configuration for logger
│   │   └── threaded_logger.c
│   ├── hotswap/         # Python file descriptor hotswap utility
│   │   ├── Makefile     # Build configuration for hotswap
│   │   └── *.py         # Python source files
│   └── Makefile         # Top-level build coordinator
└── README.md            # This file
```

## Building

The project uses a hierarchical Makefile system for building all components.

### Building Everything

From the project root or `src` directory:

```bash
make
```

This will:
1. Create output directories if needed
2. Build optimized versions of the logger
3. Create a Python virtual environment
4. Build the hotswap utility

### Building Specific Components

```bash
# Build only the logger
make logger

# Build only the hotswap utility
make hotswap

# Build release (optimized) version of logger
make release

# Build debug version of logger
make debug
```

### Cleaning

```bash
# Remove build artifacts
make clean

# Remove everything including virtual environments
make clean-all
```

## Usage

### Logger

The logger application creates the specified number of threads and writes timestamped logs continuously.

```bash
./bin/threaded_logger <logfile_path> <thread_count> <sleep_ms>
```

Example:
```bash
./bin/threaded_logger ./logs/app.log 4 500
```

This creates 4 threads, each writing to `./logs/app.log` with a 500ms delay between writes.

### Hotswap

The hotswap utility allows you to redirect a file descriptor in a running process.

```bash
./bin/hotswap --pid <PID> --from <ORIGINAL_PATH> --to <NEW_PATH>
```

Example:
```bash
./bin/hotswap --pid 1234 --from ./logs/app.log --to ./logs/app_new.log
```

This redirects file operations on `./logs/app.log` to `./logs/app_new.log` for process 1234.

## Development

For logger development, both optimized and debug builds are available:
- `./bin/threaded_logger` (optimized build)
- `./bin/threaded_logger_debug` (with debug symbols)

The debug build is useful when testing the hotswap utility with a debugger like GDB.

## License

This project is licensed under the MIT License with attribution requirement.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, and to permit persons to whom the software is furnished to do so, subject to the following condition:

Attribution to Dr. Nate Bachmeier (github/dr-natetorious) must be included in all copies or substantial portions of the software.
