import json

from moto import mock_aws

from document_intake.aws import client
from document_intake.config import Settings
from document_intake.local_setup import bootstrap

SETTINGS = Settings(_env_file=None)


@mock_aws
def test_bootstrap_creates_all_resources():
    bootstrap(SETTINGS)

    buckets = {b["Name"] for b in client("s3", SETTINGS).list_buckets()["Buckets"]}
    assert SETTINGS.originals_bucket in buckets

    tables = client("dynamodb", SETTINGS).list_tables()["TableNames"]
    assert SETTINGS.documents_table in tables

    sqs = client("sqs", SETTINGS)
    intake_url = sqs.get_queue_url(QueueName=SETTINGS.intake_queue)["QueueUrl"]
    sqs.get_queue_url(QueueName=SETTINGS.review_queue)
    redrive = json.loads(
        sqs.get_queue_attributes(QueueUrl=intake_url, AttributeNames=["RedrivePolicy"])[
            "Attributes"
        ]["RedrivePolicy"]
    )
    assert redrive["deadLetterTargetArn"].endswith(SETTINGS.intake_dlq)
    assert int(redrive["maxReceiveCount"]) == SETTINGS.max_receive_count


@mock_aws
def test_bootstrap_is_idempotent():
    bootstrap(SETTINGS)
    bootstrap(SETTINGS)
