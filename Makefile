SHELL = /bin/bash

ifndef VIRTUAL_ENV
WITH_VENV := poetry run
else
WITH_VENV :=
endif
PYTHON := $(WITH_VENV) python

init:
	mkdir -p download/raw

.PHONY: zanmei
zanmei: init
	$(PYTHON) zanmei.py -v 1

.PHONY: hoctoga
hoctoga: init
	$(PYTHON) hoctoga.py -v 1

.PHONY: hoctoga
hoc5: init
	$(PYTHON) hoc5.py -v 1

poetry-install:
	poetry install

poetry-update:
	poetry update
