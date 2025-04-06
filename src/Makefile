# Top-level Makefile for logfile-hotswap project
#
# This Makefile coordinates building both the logger and hotswap components
# from the ./src directory

SUBDIRS = logger hotswap
PROJECT_ROOT = ../
BIN_DIR = $(PROJECT_ROOT)bin

.PHONY: all clean debug release check $(SUBDIRS)

# Default target builds everything
all: $(BIN_DIR) $(SUBDIRS)

# Create bin directory if it doesn't exist
$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Target to build only the logger component
logger:
	@echo "Building logger component..."
	$(MAKE) -C $@ all

# Target to build only the hotswap component
hotswap:
	@echo "Building hotswap component..."
	$(MAKE) -C $@ all

# Target to build release version of logger
release: $(BIN_DIR)
	@echo "Building release version of logger..."
	$(MAKE) -C logger release

# Target to build debug version of logger
debug: $(BIN_DIR)
	@echo "Building debug version of logger..."
	$(MAKE) -C logger debug

# Check environment for hotswap component
check:
	@echo "Checking hotswap build environment..."
	$(MAKE) -C hotswap check-env

# Clean everything
clean:
	@echo "Cleaning all components..."
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir clean; \
	done
	rmdir --ignore-fail-on-non-empty $(BIN_DIR)

# Clean everything including virtual environments
clean-all: clean
	@echo "Deep cleaning all components and environments..."
	-$(MAKE) -C hotswap clean-all