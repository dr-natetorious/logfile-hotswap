#!/bin/bash
# Build script for logfile-hotswap using Bazel

set -e  # Exit on error

# Display help information
show_help() {
    echo "Logfile Hotswap Build Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --all            Build all components (default)"
    echo "  --logger         Build only the logger components"
    echo "  --hotswap        Build only the hotswap utility"
    echo "  --release        Build in release mode (default)"
    echo "  --debug          Build in debug mode"
    echo "  --clean          Clean build artifacts"
    echo "  --help           Display this help message"
    echo ""
}

# Default values
BUILD_ALL=true
BUILD_LOGGER=false
BUILD_HOTSWAP=false
BUILD_MODE="release"
CLEAN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            BUILD_ALL=true
            BUILD_LOGGER=false
            BUILD_HOTSWAP=false
            ;;
        --logger)
            BUILD_ALL=false
            BUILD_LOGGER=true
            ;;
        --hotswap)
            BUILD_ALL=false
            BUILD_HOTSWAP=true
            ;;
        --release)
            BUILD_MODE="release"
            ;;
        --debug)
            BUILD_MODE="debug"
            ;;
        --clean)
            CLEAN=true
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo "Cleaning build artifacts..."
    bazel clean
    # Also clean bin directory since it's outside of Bazel's control
    rm -rf bin/
    echo "Clean completed."
    
    # Exit if only clean was requested
    if [ "$BUILD_ALL" = false ] && [ "$BUILD_LOGGER" = false ] && [ "$BUILD_HOTSWAP" = false ]; then
        exit 0
    fi
fi

# Create bin directory if it doesn't exist
mkdir -p bin

# Set Bazel build configuration based on mode
CONFIG_FLAG="--config=$BUILD_MODE"

# Build the requested components
if [ "$BUILD_ALL" = true ] || [ "$BUILD_LOGGER" = true ] && [ "$BUILD_HOTSWAP" = true ]; then
    echo "Building all components in $BUILD_MODE mode..."
    bazel build $CONFIG_FLAG //...
elif [ "$BUILD_LOGGER" = true ]; then
    echo "Building logger components in $BUILD_MODE mode..."
    bazel build $CONFIG_FLAG //src/logger:all
elif [ "$BUILD_HOTSWAP" = true ]; then
    echo "Building hotswap utility in $BUILD_MODE mode..."
    bazel build $CONFIG_FLAG //src/hotswap:all
fi

echo "Build completed successfully."