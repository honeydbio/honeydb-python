codestyle:
	pycodestyle setup.py
	pycodestyle honeydb/__init__.py
	pycodestyle honeydb/api/__init__.py
	pycodestyle honeydb/api/client.py
	pycodestyle honeydb/bin/honeydb
	pycodestyle example.py

fix-codestyle:
	autopep8 --in-place --aggressive setup.py
	autopep8 --in-place --aggressive honeydb/__init__.py
	autopep8 --in-place --aggressive honeydb/api/__init__.py
	autopep8 --in-place --aggressive honeydb/api/client.py
	autopep8 --in-place --aggressive honeydb/bin/honeydb
	autopep8 --in-place --aggressive example.py

lint:
	pylint setup.py
	pylint honeydb/__init__.py
	#pylint honeydb/api/__init__.py
	pylint honeydb/api/client.py
	pylint honeydb/bin/honeydb
	pylint --disable=W example.py

env:
	virtualenv -p python .env
	source .env/bin/activate \
	&& pip install --upgrade pip \
	&& pip install --upgrade setuptools \
	&& pip install --upgrade requests pyopenssl twine

env3:
	python3 -m venv .env3
	source .env3/bin/activate \
	&& pip3 install --upgrade pip \
	&& pip3 install --upgrade setuptools \
	&& pip3 install --upgrade requests pyopenssl wheel twine

install:
	pip install --upgrade requests pylint pycodestyle

wheel:
	-rm dist/*
	python setup.py bdist_wheel --universal

dev-install:
	-pip uninstall honeydb
	pip install dist/*

publish:
	twine upload --skip-existing dist/*

clean:
	find . -name "*.pyc" -type f -delete
	rm -rf dist
	rm -rf build
