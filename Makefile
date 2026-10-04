VENV 	= .venv
BIN 	= $(VENV)/bin
PIP 	= $(BIN)/pip
PYTHON 	= $(BIN)/python3
FLAKE8 	= $(BIN)/flake8
MYPY 	= $(BIN)/mypy
FLAGS 	= --warn-return-any\
		  --warn-unused-ignores\
		  --ignore-missing-imports\
		  --disallow-untyped-defs\
		  --check-untyped-defs\

.PHONY: install run debug lint lint-strict

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install -r requirements.txt

run: install
	$(PYTHON) -m src

debug: install
	$(PYTHON) -m pdb src

clean:
	rm -rf */__pycache__
	rm -rf .mypy_cache

fclean: clean
	rm -rf $(VENV)

lint: install
	$(FLAKE8) src
	$(MYPY) $(FLAGS) src

lint-strict: install
	$(FLAKE8) src
	$(MYPY) --strict src
