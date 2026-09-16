"""
Unit tests for SecretsBroker credential isolation and redaction.
"""


from src.application.secrets_broker import SecretsBroker


def test_secrets_broker_registration_and_retrieval() -> None:
    broker = SecretsBroker()
    broker.register_secret("secret/api_key", "sk-proj-123456789")

    assert broker.get_secret("secret/api_key") == "sk-proj-123456789"
    assert broker.get_secret("non_existent") is None


def test_secrets_broker_redaction_string_and_dict() -> None:
    broker = SecretsBroker()
    broker.register_secret("secret/token", "super_secret_token_abc")

    raw_text = "Header Authorization: Bearer super_secret_token_abc for request."
    redacted_text = broker.redact(raw_text)
    assert "super_secret_token_abc" not in redacted_text
    assert "[REDACTED_SECRET]" in redacted_text

    raw_dict = {
        "status": "success",
        "details": {"key": "super_secret_token_abc", "other": "normal_data"},
        "logs": ["Auth with super_secret_token_abc successful"],
    }
    redacted_dict = broker.redact(raw_dict)
    assert redacted_dict["details"]["key"] == "[REDACTED_SECRET]"
    assert redacted_dict["logs"][0] == "Auth with [REDACTED_SECRET] successful"
