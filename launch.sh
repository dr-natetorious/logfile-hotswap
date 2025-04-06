#!/bin/bash
set -e

# This script should be located at $(PROJECT_ROOT)/devbox

# Script to build the bazel-runner Docker image, validate the build, and run an ephemeral container
# with the project root mounted to /workspace and an interactive bash shell
# This script is stored at $(PROJECT_ROOT)/devbox

# Configuration
# Find the git root directory first
PROJECT_ROOT=$(git rev-parse --show-toplevel)
DOCKERFILE_PATH="${PROJECT_ROOT}/.docker/Dockerfile"
IMAGE_NAME="bazel-runner"
CONTAINER_NAME="bazel-runner-container"
MOUNT_PATH="${PROJECT_ROOT}:/workspace"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=== Starting Docker workflow ==="

# Step 1: Build the Dockerfile
echo "Step 1: Building Docker image from ${DOCKERFILE_PATH}..."
if sudo docker build -t ${IMAGE_NAME} -f ${DOCKERFILE_PATH} .; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker image build failed${NC}"
    exit 1
fi

# Step 2: Validate the build was successful
echo "Step 2: Validating Docker image..."
if sudo docker image inspect ${IMAGE_NAME} > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker image validation successful${NC}"
else
    echo -e "${RED}✗ Docker image validation failed${NC}"
    exit 1
fi

# Step 3 & 4: Run container with project root mounted and interactive bash shell
# Step 5: Make container ephemeral (--rm flag)
echo "Step 3 & 4: Starting ephemeral container with interactive bash shell..."
echo "Mounting project root to /workspace"
echo -e "${GREEN}Container will be automatically removed when exited${NC}"
echo -e "To exit the container, type '${GREEN}exit${NC}'"
echo "=== Entering container shell ==="

sudo docker run --rm -it \
    --name ${CONTAINER_NAME} \
    -v ${MOUNT_PATH} \
    --user $(id -u):$(id -g) \
    --entrypoint /bin/bash \
    ${IMAGE_NAME} 

echo "=== Container session ended ==="