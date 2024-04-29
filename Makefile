run-checks:
	cd app && isort .
	cd app && black .
	cd app && mypy .