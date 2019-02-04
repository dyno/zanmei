SHELL = /bin/bash

ifndef VIRTUAL_ENV
WITH_VENV := pipenv run
else
WITH_VENV :=
endif
PYTHON := $(WITH_VENV) python

.PHONY: download
download:
	pipenv run python zanmei.py -v 1

.PHONY: pipenv
pipenv:
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
