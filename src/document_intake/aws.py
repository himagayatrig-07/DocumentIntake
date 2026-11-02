"""boto3 clients that point at the local moto server when AWS_ENDPOINT_URL is set."""

import boto3

from document_intake.config import Settings, get_settings


def client(service: str, settings: Settings | None = None):
    settings = settings or get_settings()
    return boto3.client(
        service,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )
