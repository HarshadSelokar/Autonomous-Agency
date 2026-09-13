"""
MeetingTranscript Domain Entity for Phase 6.
Preserves speaker identity, timestamps, and discussion history.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


@dataclass
class MeetingTranscriptEntry:
    speaker_employee_id: str
    content: str
    speaker_agent_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.speaker_employee_id or not self.speaker_employee_id.strip():
            raise ObjectiveValidationError("Transcript entry speaker_employee_id cannot be empty.")
        if not self.content or not self.content.strip():
            raise ObjectiveValidationError("Transcript entry content cannot be empty.")


@dataclass
class MeetingTranscript:
    meeting_id: str
    entries: list[MeetingTranscriptEntry] = field(default_factory=list)
    summary: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_entry(
        self,
        speaker_employee_id: str,
        content: str,
        speaker_agent_id: str | None = None,
    ) -> MeetingTranscriptEntry:
        entry = MeetingTranscriptEntry(
            speaker_employee_id=speaker_employee_id,
            content=content,
            speaker_agent_id=speaker_agent_id,
        )
        self.entries.append(entry)
        self.updated_at = datetime.now(UTC)
        return entry
