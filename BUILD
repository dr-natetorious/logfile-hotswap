package(default_visibility = ["//visibility:public"])

exports_files([
    "LICENSE",
    "README.md",
    "requirements.txt",
])

# Add a filegroup that serves as a launcher for automated builds
filegroup(
    name = "all",
    srcs = [
        "//src/logger:all",
        "//src/hotswap:all",
    ],
)