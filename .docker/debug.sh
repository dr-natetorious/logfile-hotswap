#!/bin/bash
set -e

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}" && pwd)"
DOCKER_IMAGE_NAME="bazel-runner:ubuntu24"
DOCKERFILE_PATH="${REPO_ROOT}/.docker/Dockerfile"
BUILD_OUTPUT="${HOME}/.cache/bazel-output"

# Ensure build output directory exists
mkdir -p "${BUILD_OUTPUT}"

# Check if Docker image exists, build if it doesn't
if ! docker images ${DOCKER_IMAGE_NAME} | grep -q ${DOCKER_IMAGE_NAME}; then
  echo "Building Docker image ${DOCKER_IMAGE_NAME}..."
  docker build -t ${DOCKER_IMAGE_NAME} -f ${DOCKERFILE_PATH} .
fi

echo "Starting interactive shell in the container..."
docker run --rm -it \
  -e USER="$(id -u)" \
  -u="$(id -u):$(id -g)" \
  -v "${REPO_ROOT}:/workspace" \
  -v "${BUILD_OUTPUT}:/tmp/build_output" \
  -w "/workspace" \
  --entrypoint /bin/bash
  ${DOCKER_IMAGE_NAME}
