run-checks:
	isort .
	black . -l 120
	mypy .

build:
	docker compose build


run-project:
	docker compose up