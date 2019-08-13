default: test


test: env
	.env/bin/pytest -x tests --cov=mitba --cov-report=html

env: .env/.up-to-date


.env/.up-to-date: setup.py Makefile setup.cfg
	virtualenv --no-site-packages .env
	.env/bin/pip install -e .[testing]
	touch $@

