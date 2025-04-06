FROM ubuntu:24.04

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    gnupg \
    lsb-release \
    git \
    unzip \
    wget \
    python3-virtualenv

RUN apt install apt-transport-https curl gnupg -y
RUN curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor >bazel-archive-keyring.gpg
RUN mv bazel-archive-keyring.gpg /usr/share/keyrings
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" |  tee /etc/apt/sources.list.d/bazel.list

RUN apt update -y && apt install -y bazel

# Set up workspace directory
WORKDIR /workspace

# Add entrypoint script
COPY ./.docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# # Add repositories for Bazel and newer Python
# sudo apt install apt-transport-https curl gnupg -y
# curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor >bazel-archive-keyring.gpg
# sudo mv bazel-archive-keyring.gpg /usr/share/keyrings
# echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
# # Install GCC, Python 3.12, and Bazel
# RUN apt-get update && apt-get install -y \
#     gcc-11 \
#     g++-11 \
#     python3.12 \
#     python3.12-venv \
#     python3.12-dev \
#     python3-pip \
#     bazel-7.6.1 \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# # Set GCC 11 as default (has good C++20 support)
# RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 110 \
#     && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 110 \
#     && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 120

# # Create symlink for Bazel
# RUN ln -s /usr/bin/bazel-7.6.1 /usr/bin/bazel

# Set up working directory 
WORKDIR /workspace

# # Verify versions
# RUN gcc --version && g++ --version && python3 --version && bazel --version