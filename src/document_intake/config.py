"""Settings loaded from environment variables (and a local .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    # Set to http://localhost:4566 to use the local moto server; leave unset for real AWS.
    aws_endpoint_url: str | None = None

    originals_bucket: str = "document-intake-originals"
    intake_queue: str = "document-intake"
    intake_dlq: str = "document-intake-dlq"
    review_queue: str = "document-review"
    documents_table: str = "documents"
    # Deliveries before a failing message moves to the dead-letter queue.
    max_receive_count: int = 3

    anthropic_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
