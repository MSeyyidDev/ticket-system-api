# ticket-system-api — common developer tasks
# Usage: make <target>

PYTHON ?= python
VENV ?= .venv

ifeq ($(OS),Windows_NT)
	PY := $(VENV)/Scripts/python.exe
	PIP := $(VENV)/Scripts/pip.exe
else
	PY := $(VENV)/bin/python
	PIP := $(VENV)/bin/pip
endif

.PHONY: help install seed run test lint clean

help:
	@echo "Targets:"
	@echo "  install   Create venv and install dependencies"
	@echo "  seed      Populate the SQLite database with synthetic data"
	@echo "  run       Start the Uvicorn dev server on http://127.0.0.1:8000"
	@echo "  test      Run the pytest test suite"
	@echo "  lint      Quick syntax check via py_compile"
	@echo "  clean     Remove caches and the local SQLite database"

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

seed:
	$(PY) -m app.seed

run:
	$(PY) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(PY) -m pytest -v

lint:
	$(PY) -m compileall -q app tests

clean:
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__
	rm -f tickets.db test_tickets.db
