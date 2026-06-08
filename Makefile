.PHONY: test install smoke

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests

smoke:
	python -m recallgate.cli --help
