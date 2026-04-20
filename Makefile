PYTHON=python

.PHONY: install test eval api index ask

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest

eval:
	$(PYTHON) scripts/run_eval.py

api:
	$(PYTHON) -m uvicorn app.main:app --reload

index:
	$(PYTHON) -m app.cli index

ask:
	$(PYTHON) -m app.cli ask "When must security incidents be reported?"
