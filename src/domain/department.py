"""
Department Domain Entity.
Minimal organizational unit entity.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Department:
    id: str
    name: str
    code: str
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
