CC = gcc
CFLAGS = -Wall -Wextra -pthread
PROJECT_ROOT = ../../
BIN_DIR = $(PROJECT_ROOT)bin
TARGET = $(BIN_DIR)/threaded_logger

all: $(BIN_DIR) $(TARGET)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(TARGET): threaded_logger.c | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGET)
	rmdir --ignore-fail-on-non-empty $(BIN_DIR)