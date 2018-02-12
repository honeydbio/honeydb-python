codestyle:
	pycodestyle setup.py
	pycodestyle honeydb/__init__.py
	pycodestyle honeydb/api/__init__.py
	pycodestyle honeydb/api/client.py
	pycodestyle example.py

fix-codestyle:
	autopep8 --in-place --aggressive setup.py
	autopep8 --in-place --aggressive honeydb/__init__.py
	autopep8 --in-place --aggressive honeydb/api/__init__.py
	autopep8 --in-place --aggressive honeydb/api/client.py
	autopep8 --in-place --aggressive example.py

lint:
	pylint setup.py
	pylint honeydb/__init__.py
	pylint honeydb/api/__init__.py
	pylint honeydb/api/client.py
	pylint --disable=W example.py

env:
	virtualenv -p python .env
	source .env/bin/activate \
	&& pip install --upgrade pip \
	&& pip install --upgrade setuptools \
	&& pip install --upgrade requests pyopenssl twine

env3:
	virutalenv -p python3 .env3
	source .env/bin/activate \
	&& pip3 install --upgrade pip \
	&& pip3 install --upgrade setuptools \
	&& pip3 install --upgrade requests pyopenssl twine

wheel:
	python setup.py bdist_wheel --universal

publish:
	twine upload dist/*

clean:
	find . -name "*.pyc" -type f -delete
	rm -rf dist
	rm -rf build