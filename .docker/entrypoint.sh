#!/bin/bash
set -e

# Create workspace directory if it doesn't exist
mkdir -p /workspace

# If no arguments, start a shell
if [ $# -eq 0 ]; then
  exec /bin/bash
else
  # Run bazel with provided arguments
  exec bazel "$@"
fi