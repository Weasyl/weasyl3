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
all: .stamp-ve .stamp-egg-info assets

# Creates python environment
.stamp-ve: etc/requirements.txt
	test -e ve || { $(PYVENV) ve; ve/bin/pip install -U pip setuptools; }
	ve/bin/pip install -i $(PYPI) -r $< $(USE_WHEEL)
	touch $@

# Installs weasyl package in develop mode
.stamp-egg-info: setup.py .stamp-ve
	ve/bin/pip install -i $(PYPI) $(USE_WHEEL) $(EDITABLE) '.[development]'
	touch $@

# Vagrant/libweasyl setup

libweasyl:
	git clone gitlab@gitlab.i.weasyl.com:weasyl3/libweasyl.git
	ln -s ../ve libweasyl

.PHONY: install-libweasyl
install-libweasyl: .stamp-ve .stamp-egg-info libweasyl
	ve/bin/pip install -i $(PYPI) $(USE_WHEEL) -Ue libweasyl

.PHONY: host-install-libweasyl
host-install-libweasyl: .vagrant
	vagrant ssh -c 'cd weasyl3 && make install-libweasyl'

.vagrant:
	vagrant up

.PHONY: setup-vagrant
setup-vagrant: libweasyl .vagrant

.PHONY: upgrade-db
upgrade-db: libweasyl
	cd $< && make upgrade-db

.PHONY: host-upgrade-db
host-upgrade-db: .vagrant
	vagrant ssh -c 'cd weasyl3 && make upgrade-db'

.PHONY: test
test: .stamp-ve .stamp-egg-info
	ve/bin/coverage run ve/bin/py.test weasyl
	ve/bin/coverage report -m
	ve/bin/coverage html

.PHONY: host-test
host-test: .vagrant
	vagrant ssh -c 'cd weasyl3 && make test'

.PHONY: test-all
test-all: libweasyl test
	cd $< && make tox

.PHONY: host-test-all
host-test-all: .vagrant
	vagrant ssh -c 'cd weasyl3 && make test-all'

.PHONY: docs
docs: libweasyl .stamp-egg-info
	cd libweasyl && make docs
	cd docs && make html SPHINXBUILD=../ve/bin/sphinx-build

.PHONY: host-docs
host-docs: .vagrant
	vagrant ssh -c 'cd weasyl3 && make docs'

# Asset pipeline

.stamp-node: package.json
	npm install
	touch $@

.stamp-weasyl-static: .stamp-node $(ASSETS) Gruntfile.js
	node_modules/.bin/grunt
	touch $@

.PHONY: assets
assets: .stamp-weasyl-static

.PHONY: watch
watch: .stamp-node
	node_modules/.bin/grunt watch

# Run local server
.PHONY: run
run: .stamp-ve .stamp-egg-info assets
	ve/bin/pserve --app-name main --server-name main etc/development.ini

.PHONY: host-run
host-run: .vagrant
	vagrant ssh -c 'cd weasyl3 && make run'

.PHONY: shell
shell: .stamp-ve .stamp-egg-info
	ve/bin/pshell etc/development.ini

.PHONY: host-shell
host-shell: .vagrant
	vagrant ssh -c 'cd weasyl3 && make shell'

.PHONY: clean
clean:
	find weasyl -type f -name '*.py[co]' -delete

.PHONY: distclean
distclean: clean
	rm -rf ve
	rm -rf weasyl.egg-info
	rm -rf node_modules
	rm -rf .stamp-*
	git clean -fdx weasyl/static

# Phony target to run flake8 pre-commit
.PHONY: check
check: .stamp-egg-info
	git diff HEAD | ve/bin/flake8 --config setup.cfg --statistics --diff

# Phony target to run flake8 on everything
.PHONY: check-all
check-all: .stamp-egg-info
	ve/bin/flake8 --config setup.cfg --statistics

# Phony target to run flake8 on the last commit
.PHONY: check-commit
check-commit: .stamp-egg-info
	git show | ve/bin/flake8 --config setup.cfg --statistics --diff
