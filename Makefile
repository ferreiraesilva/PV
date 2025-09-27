.PHONY: run lint format test

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff .
	black --check .

format:
	black .

test:
	pytest --cov=app --cov-report=term-missing
