# Weasyl makefile

#
# Variables
#

PYVENV ?= pyvenv

# URL of package index
PYPI := https://pypi.weasyl.com/

# Whether to use wheels
USE_WHEEL := --no-use-wheel

# Whether to install weasyl editable
EDITABLE := -e

# All of the asset files
ASSETS := $(shell find assets -type f)

#
# Rules
#

# Catch-all
all: ve assets

# Creates python environment
ve: etc/requirements.txt
	test -e $@ || { $(PYVENV) $@; $@/bin/pip install -U pip setuptools; }
	$@/bin/pip install -i $(PYPI) -r $< $(USE_WHEEL)
	touch $@

# Installs weasyl package in develop mode
weasyl.egg-info: setup.py ve
	ve/bin/pip install $(EDITABLE) .
	touch $@

node_modules: package.json
	npm install
	touch node_modules

weasyl/static: node_modules $(ASSETS)
	$</.bin/grunt
	touch weasyl/static

.PHONY: assets
assets: weasyl/static

# Run local server
.PHONY: run
run: ve weasyl.egg-info assets
	$</bin/pserve --app-name main --server-name main etc/development.ini

.PHONY: shell
shell: ve weasyl.egg-info
	$</bin/pshell etc/development.ini

.PHONY: clean
clean:
	find weasyl -type f -name '*.py[co]' -delete

.PHONY: distclean
distclean: clean
	rm -rf ve
	rm -rf weasyl.egg-info

# Phony target to run flake8 pre-commit
.PHONY: check
check:
	git diff HEAD | ve/bin/flake8 --config setup.cfg --statistics --diff

# Phony target to run flake8 on everything
.PHONY: check-all
check-all:
	ve/bin/flake8 --config setup.cfg --statistics

# Phony target to run flake8 on the last commit
.PHONY: check-commit
check-commit:
	git show | ve/bin/flake8 --config setup.cfg --statistics --diff
