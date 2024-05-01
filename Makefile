run-checks:
	isort .
	black . -l 120
	mypy .