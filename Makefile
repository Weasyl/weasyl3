# Weasyl makefile

#
# Variables
#


# URL of package index
PYPI := https://pypi.weasyl.com/

#
# Rules
#

# Catch-all
all: ve

# Creates python environment
ve: etc/requirements.txt
	test -e $@ || { pyvenv $@; $@/bin/pip install -U pip setuptools; }
	$@/bin/pip install -i $(PYPI) -r etc/requirements.txt
	touch $@
