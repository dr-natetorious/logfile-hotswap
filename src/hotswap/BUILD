load("@rules_python//python:defs.bzl", "py_binary")

package(default_visibility = ["//visibility:public"])

py_binary(
    name = "hotswap",
    srcs = glob(["*.py"]),
    main = "main.py",
    # Dependencies removed to simplify
)

# Create deployable file in the bin directory
genrule(
    name = "copy_to_bin",
    srcs = [":hotswap"],
    outs = ["bin_copy_complete"],
    cmd = """
        mkdir -p $(GENDIR)/../../bin
        cp $(location :hotswap) $(GENDIR)/../../bin/hotswap
        chmod +x $(GENDIR)/../../bin/hotswap
        touch $@
    """,
)

# Group all targets for top-level build
filegroup(
    name = "all",
    srcs = [
        ":hotswap",
        ":copy_to_bin",
    ],
)