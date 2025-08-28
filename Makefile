
install:
	uv sync --group dev --group test

test: install
	uv run pytest tests/

cov: install
	uv run pytest --cov=wandern --cov-report=term-missing tests/

cov-html: install
	uv run pytest --cov=wandern --cov-report=html --cov-report=term-missing tests/
