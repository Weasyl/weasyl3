# Weasyl makefile

#
# Variables
#

PYVENV ?= pyvenv

# URL of package index
PYPI := https://pypi.weasyl.com/

#
# Rules
#

# Catch-all
all: ve

# Creates python environment
ve: etc/requirements.txt
	test -e $@ || { $(PYVENV) $@; $@/bin/pip install -U pip setuptools; }
	$@/bin/pip install -i $(PYPI) -r etc/requirements.txt
	touch $@

.PHONY: clean
clean:
	find weasyl -type f -name '*.py[co]' -delete

.PHONY: distclean
distclean: clean
	rm -rf ve
