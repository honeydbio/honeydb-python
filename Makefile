.PHONY: env format format-check lint lint-fix test build publish local-install update-from-upstream clean

PY ?= .env/bin/python

env:
	python3 -m venv .env
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install --upgrade -e ".[dev]"

format:
	$(PY) -m ruff format .

format-check:
	$(PY) -m ruff format --check .

lint:
	$(PY) -m ruff check .

lint-fix:
	$(PY) -m ruff check --fix .

test:
	$(PY) -m pytest

build:
	-rm -rf dist
	$(PY) -m build

publish:
	$(PY) -m twine upload --skip-existing dist/*

local-install:
	-$(PY) -m pip uninstall -y honeydb
	$(PY) -m pip install dist/*.whl

update-from-upstream:
	# update master branch from honeydbio
	# first add upstream with: git remote add upstream https://github.com/honeydbio/honeydb-python.git
	git fetch upstream
	git checkout master
	git merge upstream/master
	git push origin master

clean:
	find . -name "*.pyc" -type f -delete
	rm -rf dist build .pytest_cache .ruff_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
