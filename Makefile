SHELL = /bin/bash

ifndef VIRTUAL_ENV
WITH_VENV := poetry run
else
WITH_VENV :=
endif
PYTHON := $(WITH_VENV) python

OPT := -v 1

SUNDAY := $(shell gdate -d "next sunday" +"%Y-%m-%d")

#-------------------------------------------------------------------------------
# online resources

.PHONY: zanmei
zanmei:
	$(PYTHON) zanmei.py $(OPT)

.PHONY: hoctoga
hoctoga:
	$(PYTHON) hoctoga.py $(OPT)

.PHONY: hoc5
hoc5:
	$(PYTHON) hoc5.py $(OPT)


.PHONY: mvccc
mvccc:
	$(PYTHON) mvccc.py $(OPT)


.PHONY: stats
stats:
	$(PYTHON) stats.py $(OPT)

bible_big5:
	cd download && curl -L -O http://download.o-bible.com:8080/hb5.gz && gunzip hb5.gz

download: zanmei hoctoga hoc5 mvccc bible_big5

#-------------------------------------------------------------------------------
# create slides for sunday service
.PHONY: pptx
pptx:
	$(PYTHON) slides.py $(OPT) --pptx=$(SUNDAY).pptx --flagfile=services/$(SUNDAY).flags
slides:pptx

# extract text from a pptx file
pptx_to_text:
ifdef PPTX
	$(PYTHON) slides.py --extract_only --pptx $(PPTX)
endif

#-------------------------------------------------------------------------------
# development related
.PHONY: ipython
ipython:
	poetry run ipython

poetry-install:
	poetry install

poetry-update:
	poetry update
