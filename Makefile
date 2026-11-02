.PHONY: install aws bootstrap test lint format

install:
	uv sync

# Run the local AWS emulator (S3, SQS, DynamoDB) in the foreground on port 4566 (5000 is taken by macOS AirPlay).
aws:
	uv run moto_server -p 4566

# Create the bucket, queues and table in the running emulator.
bootstrap:
	uv run --env-file .env python -m document_intake.local_setup

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .
