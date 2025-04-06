#!/bin/bash
# Build script for logfile-hotswap using Bazel in a Docker container

set -e  # Exit on error

# Add color to output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the absolute path to the git repository
REPO_PATH=$(cd "$(dirname "$0")" && pwd)
echo -e "${BLUE}Repository path: ${REPO_PATH}${NC}"

# Create a directory for the build outputs
BUILD_OUTPUT="${HOME}/.cache/logfile-hotswap-bazel"
mkdir -p "${BUILD_OUTPUT}"
echo -e "${BLUE}Build output cache: ${BUILD_OUTPUT}${NC}"

# Display help information
show_help() {
    echo -e "${GREEN}Logfile Hotswap Docker Build Script${NC}"
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
    echo "  --no-sudo        Don't use sudo with docker commands"
    echo ""
}

# Default values
BUILD_TARGET="//src/hotswap:hotswap //src/logger:all"  # Explicit targets instead of //...
BUILD_MODE="release"
CLEAN=false
USE_SUDO=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            BUILD_TARGET="//src/hotswap:hotswap //src/logger:all"
            ;;
        --logger)
            BUILD_TARGET="//src/logger:all"
            ;;
        --hotswap)
            BUILD_TARGET="//src/hotswap:all"
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
        --no-sudo)
            USE_SUDO=false
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
    shift
done

# Set the docker command prefix based on whether sudo is needed
DOCKER_CMD="docker"
if [ "$USE_SUDO" = true ]; then
    DOCKER_CMD="sudo docker"
    echo -e "${YELLOW}Using sudo with docker commands${NC}"
fi

# Test docker availability
echo -e "${BLUE}Testing Docker availability...${NC}"
if ! $DOCKER_CMD version > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not available. Please make sure Docker is installed and running.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker is available${NC}"

# Check if the image exists or needs to be pulled
echo -e "${BLUE}Checking for Bazel Docker image...${NC}"
if ! $DOCKER_CMD image inspect gcr.io/bazel-public/bazel:latest > /dev/null 2>&1; then
    echo -e "${YELLOW}Bazel Docker image not found. Pulling image...${NC}"
    $DOCKER_CMD pull gcr.io/bazel-public/bazel:latest
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to pull Docker image. Please check your internet connection and Docker configuration.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Successfully pulled Bazel Docker image${NC}"
else
    echo -e "${GREEN}Bazel Docker image is available${NC}"
fi

# Build the Bazel command
# Use output_base to specify a location for Bazel's output
BAZEL_CMD=""

# Add clean if requested
if [ "$CLEAN" = true ]; then
    BAZEL_CMD="clean"
    
    # Also clean bin directory since it's outside of Bazel's control
    echo -e "${YELLOW}Cleaning bin directory...${NC}"
    rm -rf "${REPO_PATH}/bin/"
    
    echo -e "${BLUE}Cleaning build artifacts...${NC}"
else
    # Set Bazel build configuration based on mode
    CONFIG_FLAG="--config=$BUILD_MODE"
    BAZEL_CMD="build $CONFIG_FLAG $BUILD_TARGET"
    
    # Create bin directory if it doesn't exist
    echo -e "${BLUE}Ensuring bin directory exists...${NC}"
    mkdir -p "${REPO_PATH}/bin"
    
    echo -e "${BLUE}Building target: ${BUILD_TARGET} in ${BUILD_MODE} mode...${NC}"
fi

# Print the full command that will be executed
FULL_DOCKER_CMD="$DOCKER_CMD run \
  -e USER=\"$(id -u)\" \
  -u=\"$(id -u)\" \
  -v \"${REPO_PATH}:${REPO_PATH}\" \
  -v \"${BUILD_OUTPUT}:/tmp/build_output\" \
  -w \"${REPO_PATH}\" \
  gcr.io/bazel-public/bazel:latest \
  --output_user_root=/tmp/build_output \
  $BAZEL_CMD"

echo -e "${YELLOW}Executing command:${NC}"
echo -e "${BLUE}$FULL_DOCKER_CMD${NC}"

# Run the Docker container with the Bazel command
$DOCKER_CMD run \
  -e USER="$(id -u)" \
  -u="$(id -u)" \
  -v "${REPO_PATH}:${REPO_PATH}" \
  -v "${BUILD_OUTPUT}:/tmp/build_output" \
  -w "${REPO_PATH}" \
  gcr.io/bazel-public/bazel:latest \
  --output_user_root=/tmp/build_output \
  $BAZEL_CMD

# Capture the exit code of the Docker run command
DOCKER_EXIT_CODE=$?

if [ $DOCKER_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Docker build failed with exit code $DOCKER_EXIT_CODE${NC}"
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo "1. Check if your Docker daemon is running"
    echo "2. Check if you have sufficient permissions to run Docker"
    echo "3. Verify that the paths exist and are accessible"
    echo "4. Check for network issues if pulling the image failed"
    exit $DOCKER_EXIT_CODE
fi

# If we're in build mode (not clean), then after the build command completes,
# we need to extract binaries from bazel-out/ into the bin/ directory
if [ "$CLEAN" = false ]; then
    echo -e "${BLUE}Copying built binaries to bin/ directory...${NC}"
    
    COPY_CMD="cp -f bazel-bin/src/logger/threaded_logger bin/ 2>/dev/null || true && \
              cp -f bazel-bin/src/logger/threaded_logger_debug bin/ 2>/dev/null || true && \
              cp -f bazel-bin/src/logger/ThreadedLogger bin/ 2>/dev/null || true && \
              cp -f bazel-bin/src/logger/ThreadedLogger_debug bin/ 2>/dev/null || true && \
              cp -f bazel-bin/src/hotswap/hotswap bin/ 2>/dev/null || true && \
              chmod +x bin/* 2>/dev/null || true"
    
    echo -e "${YELLOW}Executing copy command:${NC}"
    echo -e "${BLUE}$COPY_CMD${NC}"
    
    # Run a container to copy the files with proper permissions
    $DOCKER_CMD run \
      -e USER="$(id -u)" \
      -u="$(id -u)" \
      -v "${REPO_PATH}:${REPO_PATH}" \
      -v "${BUILD_OUTPUT}:/tmp/build_output" \
      -w "${REPO_PATH}" \
      --entrypoint "/bin/bash" \
      gcr.io/bazel-public/bazel:latest \
      -c "$COPY_CMD"
    
    # Capture the exit code of the Docker run command for copy
    COPY_EXIT_CODE=$?
    
    if [ $COPY_EXIT_CODE -ne 0 ]; then
        echo -e "${YELLOW}Warning: Some binaries may not have been copied (exit code $COPY_EXIT_CODE)${NC}"
        echo -e "${YELLOW}This is normal if you did not build all components${NC}"
    else
        echo -e "${GREEN}Binaries copied successfully${NC}"
    fi
    
    # List the binaries that were copied
    echo -e "${BLUE}Contents of bin/ directory:${NC}"
    ls -la "${REPO_PATH}/bin/"
fi

echo -e "${GREEN}Docker build completed successfully.${NC}"