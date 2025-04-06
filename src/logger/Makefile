CC = gcc
CXX = g++
CFLAGS = -Wall -Wextra -pthread
CXXFLAGS = -Wall -Wextra -pthread -std=c++20

# Ultra aggressive optimization and stripping for release
ULTRA_RELEASE_FLAGS = -O3 -DNDEBUG -fomit-frame-pointer -ffunction-sections -fdata-sections \
                      -fno-asynchronous-unwind-tables -fno-exceptions -fno-rtti \
                      -fvisibility=hidden -fvisibility-inlines-hidden \
                      -flto -fwhole-program -fno-stack-protector -fmerge-all-constants

# Extreme stripping linker flags
ULTRA_LDFLAGS = -Wl,--gc-sections,--strip-all,--discard-all,--build-id=none

PROJECT_ROOT = ../../
BIN_DIR = $(PROJECT_ROOT)bin

# C version targets
C_TARGET = $(BIN_DIR)/threaded_logger
C_DEBUG_TARGET = $(BIN_DIR)/threaded_logger_debug

# C++ version targets
CXX_TARGET = $(BIN_DIR)/ThreadedLogger
CXX_DEBUG_TARGET = $(BIN_DIR)/ThreadedLogger_debug

# C++ source files - updated to match your actual files
CXX_SOURCES = main.cpp LoggerApp.cpp ThreadLogger.cpp

all: release debug

release: c-release cpp-release

debug: c-debug cpp-debug

# C version targets
c-release: $(BIN_DIR) $(C_TARGET)
c-debug: $(BIN_DIR) $(C_DEBUG_TARGET)

# C++ version targets
cpp-release: $(BIN_DIR) $(CXX_TARGET)
cpp-debug: $(BIN_DIR) $(CXX_DEBUG_TARGET)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# C version build rules
# Production build - fully optimized and stripped
$(C_TARGET): threaded_logger.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $< -Wl,--gc-sections,--strip-all

# Debug build - with symbols and no optimization
$(C_DEBUG_TARGET): threaded_logger.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -g -O0 -o $@ $<

# C++ version build rules
# Ultra-optimized build with maximum stripping
$(CXX_TARGET): $(CXX_SOURCES) | $(BIN_DIR)
	$(CXX) $(CXXFLAGS) $(ULTRA_RELEASE_FLAGS) -o $@ $(CXX_SOURCES) $(ULTRA_LDFLAGS)
	# Additional stripping with objcopy to ensure all symbols are removed
	objcopy --strip-unneeded --strip-debug --strip-dwo --discard-all $@

# Debug build - with symbols and no optimization
$(CXX_DEBUG_TARGET): $(CXX_SOURCES) | $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -g -O0 -o $@ $(CXX_SOURCES)

verify-stripped: $(CXX_TARGET)
	@echo "Verifying stripped binary..."
	@nm -D $(CXX_TARGET) || echo "No dynamic symbols found (good)"
	@nm $(CXX_TARGET) || echo "No symbols found (good)"
	@objdump -t $(CXX_TARGET) | grep -v "no symbols" || echo "No symbols found (good)"

clean:
	rm -f $(C_TARGET) $(C_DEBUG_TARGET) $(CXX_TARGET) $(CXX_DEBUG_TARGET)
	rmdir --ignore-fail-on-non-empty $(BIN_DIR)

.PHONY: all release debug c-release c-debug cpp-release cpp-debug clean verify-stripped