# Weasyl makefile

#
# Variables
#

PYVENV ?= pyvenv

# URL of package index
PYPI := https://pypi.weasyl.com/

# Whether to use wheels
USE_WHEEL := --no-use-wheel

#
# Rules
#

# Catch-all
all: ve

# Creates python environment
ve: etc/requirements.txt
	test -e $@ || { $(PYVENV) $@; $@/bin/pip install -U pip setuptools; }
	$@/bin/pip install -i $(PYPI) -r etc/requirements.txt $(USE_WHEEL)
	touch $@

# Installs weasyl package in develop mode
weasyl.egg-info: setup.py ve
	ve/bin/python setup.py develop
	touch $@

# Run local server
.PHONY: run
run: ve weasyl.egg-info
	$</bin/pserve --app-name main --server-name main etc/development.ini

.PHONY: clean
clean:
	find weasyl -type f -name '*.py[co]' -delete

.PHONY: distclean
distclean: clean
	rm -rf ve
	rm -rf weasyl.egg-info
