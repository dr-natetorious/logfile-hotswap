cc_binary(
    name = "ThreadedLogger",
    srcs = [
        "main.cpp",
        "LoggerApp.cpp",
        "ThreadLogger.cpp",
    ],
    copts = [
        "-Wall",
        "-Wextra",
        "-pthread",
        "-std=c++20",
    ],
    linkopts = [
        "-pthread",
    ],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "ThreadedLogger_debug",
    srcs = [
        "main.cpp",
        "LoggerApp.cpp",
        "ThreadLogger.cpp",
    ],
    copts = [
        "-Wall",
        "-Wextra",
        "-pthread",
        "-std=c++20",
        "-g",
        "-O0",
    ],
    linkopts = [
        "-pthread",
    ],
    visibility = ["//visibility:public"],
)

# For the ultra-optimized version
cc_binary(
    name = "ThreadedLogger_ultra",
    srcs = [
        "main.cpp",
        "LoggerApp.cpp",
        "ThreadLogger.cpp",
    ],
    copts = [
        "-Wall",
        "-Wextra",
        "-pthread",
        "-std=c++20",
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
    ],
    linkopts = [
        "-pthread",
        "-Wl,--gc-sections,--strip-all,--discard-all,--build-id=none",
    ],
    visibility = ["//visibility:public"],
)

# C version if needed
cc_binary(
    name = "threaded_logger",
    srcs = ["threaded_logger.c"],
    copts = [
        "-Wall",
        "-Wextra",
        "-pthread",
    ],
    linkopts = [
        "-pthread",
        "-Wl,--gc-sections,--strip-all",
    ],
    visibility = ["//visibility:public"],
)

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
    linkopts = [
        "-pthread",
    ],
    visibility = ["//visibility:public"],
)