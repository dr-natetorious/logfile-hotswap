CC = gcc
CFLAGS = -Wall -Wextra -pthread
RELEASE_FLAGS = -O3 -DNDEBUG -s -fomit-frame-pointer -flto -ffunction-sections -fdata-sections
PROJECT_ROOT = ../../
BIN_DIR = $(PROJECT_ROOT)bin
TARGET = $(BIN_DIR)/threaded_logger
DEBUG_TARGET = $(BIN_DIR)/threaded_logger_debug

all: release debug

release: $(BIN_DIR) $(TARGET)

debug: $(BIN_DIR) $(DEBUG_TARGET)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Production build - fully optimized and stripped
$(TARGET): threaded_logger.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $(RELEASE_FLAGS) -o $@ $< -Wl,--gc-sections

# Debug build - with symbols and no optimization
$(DEBUG_TARGET): threaded_logger.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -g -O0 -o $@ $<

clean:
	rm -f $(TARGET) $(DEBUG_TARGET)
	rmdir --ignore-fail-on-non-empty $(BIN_DIR)

.PHONY: all release debug clean