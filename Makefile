env:
	python3 -m venv .env
	.env/bin/pip3 install --upgrade pip
	.env/bin/pip3 install --upgrade setuptools
	.env/bin/pip3 install --upgrade requests black ruff wheel twine

format-check:
	if [ -f .env/bin/black ]; then .env/bin/black --check .; else black --check .; fi

lint-check:
	if [ -f .env/bin/ruff ]; then .env/bin/ruff .; else ruff .; fi

wheel:
	-rm dist/*
	.env/bin/python setup.py bdist_wheel --universal

publish:
	.env/bin/twine upload --skip-existing dist/*

local-install:
	-.env/bin/pip3 uninstall honeydb
	.env/bin/pip3 install dist/*

update-from-upstream:
	# update master branch from honeydbio
	# first add upstream with: git remote add upstream https://github.com/honeydbio/honeydb-python.git
	git fetch upstream
	git checkout master
	git merge upstream/master
	git push origin master

clean:
	find . -name "*.pyc" -type f -delete
	rm -rf dist
	rm -rf build
