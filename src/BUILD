package(default_visibility = ["//visibility:public"])

exports_files([
    "requirements.txt",
    "LICENSE",
    "README.md",
])

# Add a filegroup that serves as a launcher for automated builds
filegroup(
    name = "all",
    srcs = [
        "//src/logger:all",
        "//src/hotswap:all",
    ],
)