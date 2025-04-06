PROJECT_ROOT = ../../
VENV_DIR = $(PROJECT_ROOT).venv
BIN_DIR = $(PROJECT_ROOT)bin
TARGET = $(BIN_DIR)/hotswap
SOURCES = $(wildcard *.py)
DEPENDENCIES = pyinstaller

.PHONY: all clean venv install-deps

all: venv $(BIN_DIR) $(TARGET)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

venv:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment in $(VENV_DIR)..."; \
		python3 -m venv $(VENV_DIR); \
	else \
		# Check if the venv structure is intact by testing for python binary \
		if [ ! -f "$(VENV_DIR)/bin/python3" ]; then \
			echo "Virtual environment exists but appears broken. Recreating..."; \
			rm -rf $(VENV_DIR); \
			python3 -m venv $(VENV_DIR); \
		else \
			echo "Using existing virtual environment"; \
		fi \
	fi
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install $(DEPENDENCIES)

$(TARGET): $(SOURCES) | $(BIN_DIR) venv
	# Combine Python files into a single executable
	$(VENV_DIR)/bin/python -m PyInstaller --onefile --clean --name hotswap \
		--distpath $(BIN_DIR) \
		--specpath $(PROJECT_ROOT)build \
		--workpath $(PROJECT_ROOT)build \
		main.py

clean:
	rm -f $(TARGET)
	rm -rf $(PROJECT_ROOT)build
	rm -f *.spec
	rmdir --ignore-fail-on-non-empty $(BIN_DIR)

clean-all: clean
	rm -rf $(VENV_DIR)

# Helper target for checking Python version and dependencies
check-env: venv
	@echo "Python version:"
	@$(VENV_DIR)/bin/python --version
	@echo "Required dependencies:"
	@$(VENV_DIR)/bin/pip list | grep -E "$(DEPENDENCIES)" || echo "Missing dependencies - run 'make install-deps'"
