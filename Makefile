env:
	python3 -m venv .env
	.env/bin/pip3 install --upgrade pip
	.env/bin/pip3 install --upgrade setuptools
	.env/bin/pip3 install --upgrade requests black ruff wheel twine

format-check:
	if [ -f .env/bin/black ]; then .env/bin/black --check .; else black --check .; fi

lint-check:
	if [ -f .env/bin/ruff ]; then .env/bin/ruff .; else ruff.; fi

wheel:
	-rm dist/*
	python setup.py bdist_wheel --universal

publish:
	twine upload --skip-existing dist/*

local-install:
	-.env/bin/pip3 uninstall honeydb
	.env/bin/pip3 install dist/*

clean:
	find . -name "*.pyc" -type f -delete
	rm -rf dist
	rm -rf build
