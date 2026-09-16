"""
Unit tests for Artifact domain entity, versioning, SHA-256 checksums, and LocalStorageProvider.
"""

from typing import Any

import pytest

from src.domain.artifact import Artifact, ArtifactStatus, compute_sha256
from src.infrastructure.storage_provider import LocalStorageProvider


def test_artifact_creation_and_checksum() -> None:
    content = b"# Analytics Architecture Report\nPostgreSQL is selected."
    checksum = compute_sha256(content)

    art = Artifact(
        id="art-100",
        workspace_id="ws-1",
        name="architecture.md",
        mime_type="text/markdown",
        size_bytes=len(content),
        checksum_sha256=checksum,
        created_by_employee_id="emp-dev",
        version=1,
    )

    assert art.id == "art-100"
    assert art.version == 1
    assert art.checksum_sha256 == checksum
    assert art.status == ArtifactStatus.ACTIVE


def test_artifact_versioning_flow() -> None:
    content_v1 = b"Version 1 Content"
    checksum_v1 = compute_sha256(content_v1)

    art_v1 = Artifact(
        id="art-v1",
        workspace_id="ws-1",
        name="report.md",
        mime_type="text/markdown",
        size_bytes=len(content_v1),
        checksum_sha256=checksum_v1,
        created_by_employee_id="emp-dev",
        version=1,
    )

    content_v2 = b"Version 2 Updated Content"
    checksum_v2 = compute_sha256(content_v2)

    art_v2 = art_v1.create_next_version(
        new_artifact_id="art-v2",
        size_bytes=len(content_v2),
        checksum_sha256=checksum_v2,
        storage_key="scratch/art-v2.md",
        creator_employee_id="emp-dev",
    )

    assert art_v1.status == ArtifactStatus.SUPERSEDED
    assert art_v2.status == ArtifactStatus.ACTIVE
    assert art_v2.version == 2
    assert art_v2.checksum_sha256 == checksum_v2


@pytest.mark.asyncio
async def test_local_storage_provider(tmp_path: Any) -> None:
    provider = LocalStorageProvider(base_dir=str(tmp_path))
    payload = b"Hello Autonomous AI Organization Platform"

    stored_path = await provider.store_bytes("payload.bin", payload)
    assert stored_path is not None

    read_data = await provider.read_bytes("payload.bin")
    assert read_data == payload

    deleted = await provider.delete_bytes("payload.bin")
    assert deleted is True
