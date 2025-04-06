# Common C++ source files
CXX_SOURCES = [
    "main.cpp",
    "LoggerApp.cpp",
    "ThreadLogger.cpp",
    "LoggerApp.hpp",
    "ThreadLogger.hpp",
]

# Common C++ compiler flags
CXX_COMMON_FLAGS = [
    "-Wall",
    "-Wextra",
    "-pthread",
    "-std=c++20",
]

# Ultra aggressive optimization flags (matching Makefile)
ULTRA_RELEASE_FLAGS = [
    "-O3",
    "-DNDEBUG",
    "-fomit-frame-pointer",
    "-ffunction-sections",
    "-fdata-sections",
    "-fno-asynchronous-unwind-tables",
    "-fno-rtti",
    "-fvisibility=hidden",
    "-fvisibility-inlines-hidden",
    "-flto",
    "-fwhole-program",
    "-fno-stack-protector",
    "-fmerge-all-constants",
]

# Extreme stripping linker flags (matching Makefile)
ULTRA_LDFLAGS = [
    "-pthread",
    "-Wl,--gc-sections,--strip-all,--discard-all,--build-id=none",
]

# Standard release linker flags
RELEASE_LDFLAGS = [
    "-pthread",
    "-Wl,--gc-sections,--strip-all",
]

# Debug linker flags
DEBUG_LDFLAGS = [
    "-pthread",
]

# C++ ultra-optimized version (matching Makefile)
cc_binary(
    name = "ThreadedLogger",
    srcs = CXX_SOURCES,
    copts = CXX_COMMON_FLAGS + ULTRA_RELEASE_FLAGS,
    linkopts = ULTRA_LDFLAGS,
    # Post-build script can be added to replicate objcopy behavior
    # Bazel doesn't directly support objcopy, so we might need a genrule for this
    visibility = ["//visibility:public"],
)

# C++ debug version
cc_binary(
    name = "ThreadedLogger_debug",
    srcs = CXX_SOURCES,
    copts = CXX_COMMON_FLAGS + [
        "-g",
        "-O0",
    ],
    linkopts = DEBUG_LDFLAGS,
    visibility = ["//visibility:public"],
)

# C version release
cc_binary(
    name = "threaded_logger",
    srcs = ["threaded_logger.c"],
    copts = [
        "-Wall",
        "-Wextra",
        "-pthread",
        "-O2",  # Added default optimization level
        "-DNDEBUG",
    ],
    linkopts = RELEASE_LDFLAGS,
    visibility = ["//visibility:public"],
)

# C version debug
cc_binary(
    name = "threaded_logger_debug",
    srcs = ["threaded_logger.c"],
    copts = [
        "-Wall",
        "-Wextra",
        "-pthread",
        "-g",
        "-O0",
    ],
    linkopts = DEBUG_LDFLAGS,
    visibility = ["//visibility:public"],
)