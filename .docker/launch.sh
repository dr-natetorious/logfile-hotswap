#!/bin/bash

# Set error handling
set -e

echo "Building Docker image 'hotswap'..."
docker build -t hotswap -f ./Dockerfile .

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "Docker image 'hotswap' built successfully!"
else
    echo "Docker build failed. Exiting."
    exit 1
fi

# Run the container with volume mount and expose debugpy port
echo "Starting container with mounted source directory and debugpy port..."
docker run -it --rm \
    -v "$(pwd)/src:/app/src" \
    -p 5678:5678 \
    hotswap

echo "Container started successfully. debugpy is accessible on port 5678."
