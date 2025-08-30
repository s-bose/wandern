
install:
	uv sync --group dev --group test

test: install
	uv run pytest tests/

cov: install
	uv run pytest --cov=wandern --cov-report=term-missing tests/

cov-html: install
	uv run pytest --cov=wandern --cov-report=html --cov-report=term-missing tests/

lint: install
	uv run ruff check

lint-fix: install
	-uv run ruff check --select I --fix
	-uv run ruff format

format: install
	uv run ruff format
