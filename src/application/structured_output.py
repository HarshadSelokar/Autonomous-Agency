"""
Structured Output Validation Subsystem.
Validates model output content against JSON schemas or Pydantic models.
"""

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from src.domain.exceptions import StructuredOutputValidationError


class StructuredOutputValidator:
    """Validates raw text or dictionary structured output against expected schemas."""

    def validate(
        self,
        content: str,
        expected_schema: dict[str, Any] | type[BaseModel] | None = None,
        preparsed_output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate structured output. Returns validated dict if valid, else raises
        StructuredOutputValidationError.
        """
        if expected_schema is None:
            # If no schema is enforced, return parsed dict if possible or raw wrapped content
            if preparsed_output is not None:
                return preparsed_output
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return {"raw_content": content}

        # Case 1: Schema is a Pydantic BaseModel class
        if isinstance(expected_schema, type) and issubclass(expected_schema, BaseModel):
            try:
                if preparsed_output is not None:
                    instance = expected_schema.model_validate(preparsed_output)
                else:
                    instance = expected_schema.model_validate_json(content)
                return instance.model_dump()
            except ValidationError as e:
                raise StructuredOutputValidationError(
                    f"Model output failed Pydantic schema validation: {e}"
                ) from e
            except json.JSONDecodeError as e:
                raise StructuredOutputValidationError(
                    f"Model output is not valid JSON for Pydantic model: {e}"
                ) from e

        # Case 2: Schema is a raw dictionary (JSON schema requirement list of keys)
        if isinstance(expected_schema, dict):
            # Parse JSON if not pre-parsed
            data = preparsed_output
            if data is None:
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise StructuredOutputValidationError(
                        f"Model output is not valid JSON string: {e}"
                    ) from e

            if not isinstance(data, dict):
                raise StructuredOutputValidationError(
                    f"Expected dictionary output schema, got '{type(data).__name__}'."
                )

            # Check required fields if specified in schema
            required_keys = expected_schema.get("required", [])
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                raise StructuredOutputValidationError(
                    f"Structured output missing required fields: {missing_keys}"
                )

            return data

        raise StructuredOutputValidationError(
            f"Unsupported validation schema type '{type(expected_schema)}'."
        )
