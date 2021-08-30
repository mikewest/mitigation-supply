all:
	python3 -m pip install -r requirements.txt --user
	python3 ./bin/fetch.py > index.html
