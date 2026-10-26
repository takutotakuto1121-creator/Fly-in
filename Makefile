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
		  --check-untyped-defs
ARG		?= maps/hard/03_ultimate_challenge.txt

.PHONY: install run debug lint lint-strict

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install -r requirements.txt

log: install
	$(PYTHON) __main__.py --log $(ARG)

run: install
	$(PYTHON) __main__.py

debug: install
	$(PYTHON) -m pdb __main__.py

clean:
	rm -rf */__pycache__
	rm -rf .mypy_cache

fclean: clean
	rm -rf $(VENV)

lint: install
	$(FLAKE8) __main__.py mapf.py parse.py visualize.py
	$(MYPY) $(FLAGS) __main__.py mapf.py parse.py visualize.py

lint-strict: install
	$(FLAKE8) __main__.py mapf.py parse.py visualize.py
	$(MYPY) --strict __main__.py mapf.py parse.py visualize.py
