"""Create the S3 bucket, SQS queues and DynamoDB table for local development.

Safe to run repeatedly: anything that already exists is left as is.
Real AWS resources will be created with infrastructure as code, not this script.
"""

import json

from document_intake.aws import client
from document_intake.config import Settings, get_settings


def create_bucket(settings: Settings) -> None:
    s3 = client("s3", settings)
    existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
    if settings.originals_bucket not in existing:
        # us-east-1 rejects an explicit LocationConstraint; other regions require one.
        kwargs = {}
        if settings.aws_region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": settings.aws_region}
        s3.create_bucket(Bucket=settings.originals_bucket, **kwargs)


def create_queues(settings: Settings) -> None:
    sqs = client("sqs", settings)
    dlq_url = sqs.create_queue(QueueName=settings.intake_dlq)["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])["Attributes"][
        "QueueArn"
    ]
    redrive = json.dumps(
        {"deadLetterTargetArn": dlq_arn, "maxReceiveCount": str(settings.max_receive_count)}
    )
    sqs.create_queue(QueueName=settings.intake_queue, Attributes={"RedrivePolicy": redrive})
    sqs.create_queue(QueueName=settings.review_queue)


def create_table(settings: Settings) -> None:
    dynamodb = client("dynamodb", settings)
    if settings.documents_table in dynamodb.list_tables()["TableNames"]:
        return
    dynamodb.create_table(
        TableName=settings.documents_table,
        AttributeDefinitions=[{"AttributeName": "document_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "document_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )


def bootstrap(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    create_bucket(settings)
    create_queues(settings)
    create_table(settings)


if __name__ == "__main__":
    settings = get_settings()
    if not settings.aws_endpoint_url:
        raise SystemExit("AWS_ENDPOINT_URL is not set; refusing to create resources in real AWS.")
    bootstrap(settings)
    print(f"Local resources ready at {settings.aws_endpoint_url}")
