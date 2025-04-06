PROJECT_ROOT = ../../
VENV_DIR = $(PROJECT_ROOT).venv
BIN_DIR = $(PROJECT_ROOT)bin
TARGET = $(BIN_DIR)/hotswap
SOURCES = $(wildcard *.py)
DEPENDENCIES = pyinstaller

# Use virtual environment binaries
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip3

.PHONY: all clean venv install-deps

all: venv install-deps $(BIN_DIR) $(TARGET)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

venv:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment in $(VENV_DIR)..."; \
		python3 -m venv $(VENV_DIR); \
	else \
		echo "Virtual environment already exists"; \
	fi

install-deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install $(DEPENDENCIES)

$(TARGET): $(SOURCES) | $(BIN_DIR) venv install-deps
	# Combine Python files into a single executable
	$(PYTHON) -m PyInstaller --onefile --clean --name hotswap \
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
	@$(PYTHON) --version
	@echo "Required dependencies:"
	@$(PIP) list | grep -E "$(DEPENDENCIES)" || echo "Missing dependencies - run 'make install-deps'"