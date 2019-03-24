SHELL = /bin/bash

ifndef VIRTUAL_ENV
WITH_VENV := poetry run
else
WITH_VENV :=
endif
PYTHON := $(WITH_VENV) python

UNAME := $(shell uname -s)
ifeq ($(UNAME),Linux)
    date = date
endif
ifeq ($(UNAME),Darwin)
    date = gdate
endif

#-------------------------------------------------------------------------------
# brew install coreutils
SUNDAY := $(shell $(date) -d "next sunday" +"%Y-%m-%d")

OPT := -v 1

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

ibibles.net:
	# download/cut/books.txt
	cd download && curl -L -O http://download.ibibles.net/cut.zip && unzip -o cut.zip

bible.cloud:
	# download/CMNUNV.epub
	cd download && curl -L -O https://bible.cloud/ebooks/epub/CMNUNV.epub
	cd download && curl -L -O https://bible.cloud/ebooks/epub/CMNUN1.epub

download: zanmei hoctoga hoc5 mvccc ibibles.net bible.cloud

#-------------------------------------------------------------------------------
.PHONY: pptx
# create slides for sunday service
pptx:
	$(PYTHON) slides.py $(OPT) --pptx=$(SUNDAY).pptx --flagfile=services/$(SUNDAY).flags
slides:pptx

.PHONY: pptx_to_text
# extract text from a pptx file
pptx_to_text:
ifdef PPTX
	$(PYTHON) slides.py --extract_only --pptx $(PPTX)
endif

.PHONY: scripture
scripture:
ifdef VERSE
	$(PYTHON) scripture.py --bible_index $(VERSE)
else
	$(PYTHON) scripture.py
endif
#-------------------------------------------------------------------------------
# development related

test:
	$(PYTHON) -m pytest --doctest-modules --capture=no --verbose

.PHONY: ipython
ipython:
	poetry run ipython

poetry-install:
	poetry install

poetry-update:
	poetry update

init: poetry-update download
