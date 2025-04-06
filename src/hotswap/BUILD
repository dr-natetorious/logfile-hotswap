load("@rules_python//python:defs.bzl", "py_binary")
load("@hotswap_deps//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

py_binary(
    name = "hotswap",
    srcs = glob(["*.py"]),
    main = "main.py",
    deps = [
        requirement("pyinstaller"),
    ],
)

# This defines a target for building the standalone binary
# similar to what PyInstaller would do
genrule(
    name = "hotswap_deploy",
    srcs = [":hotswap"],
    outs = ["hotswap_deploy.bin"],
    cmd = """
        cp $(location :hotswap) $@
        chmod +x $@
    """,
)

# Create deployable files in the bin directory
genrule(
    name = "copy_to_bin",
    srcs = [":hotswap_deploy"],
    outs = ["bin_copy_complete"],
    cmd = """
        mkdir -p $(GENDIR)/../../bin
        cp $(location :hotswap_deploy) $(GENDIR)/../../bin/hotswap
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