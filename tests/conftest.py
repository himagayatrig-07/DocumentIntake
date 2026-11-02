import pytest


@pytest.fixture(autouse=True)
def fake_aws_credentials(monkeypatch):
    """Make sure tests can never reach a real AWS account."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
