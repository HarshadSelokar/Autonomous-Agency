"""
Unit tests for StructuredOutputValidator.
"""

import pytest
from pydantic import BaseModel, Field

from src.application.structured_output import StructuredOutputValidator
from src.domain.exceptions import StructuredOutputValidationError


class UserSchema(BaseModel):
    name: str
    age: int
    tags: list[str] = Field(default_factory=list)


def test_validator_pydantic_schema_valid() -> None:
    validator = StructuredOutputValidator()
    raw_json = '{"name": "Alice", "age": 30, "tags": ["admin", "user"]}'

    res = validator.validate(content=raw_json, expected_schema=UserSchema)
    assert res["name"] == "Alice"
    assert res["age"] == 30
    assert res["tags"] == ["admin", "user"]


def test_validator_pydantic_schema_invalid_raises_error() -> None:
    validator = StructuredOutputValidator()
    raw_json = '{"name": "Alice", "age": "not-an-int"}'

    with pytest.raises(StructuredOutputValidationError) as exc:
        validator.validate(content=raw_json, expected_schema=UserSchema)

    assert "Model output failed Pydantic schema validation" in str(exc.value)


def test_validator_dict_schema_required_fields() -> None:
    validator = StructuredOutputValidator()
    dict_schema = {"required": ["summary", "confidence"]}

    # Valid
    valid_res = validator.validate(
        content='{"summary": "Test", "confidence": 0.95}',
        expected_schema=dict_schema,
    )
    assert valid_res["summary"] == "Test"

    # Missing required field
    with pytest.raises(StructuredOutputValidationError) as exc:
        validator.validate(
            content='{"summary": "Test"}',
            expected_schema=dict_schema,
        )

    assert "missing required fields: ['confidence']" in str(exc.value)


def test_validator_preparsed_output() -> None:
    validator = StructuredOutputValidator()
    preparsed = {"name": "Bob", "age": 25}

    res = validator.validate(content="", expected_schema=UserSchema, preparsed_output=preparsed)
    assert res["name"] == "Bob"
    assert res["age"] == 25
