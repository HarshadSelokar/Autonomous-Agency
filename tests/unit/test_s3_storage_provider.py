"""Unit tests for S3 Storage Provider and Storage Factory."""

import pytest
from src.infrastructure.config import Settings
from src.infrastructure.s3_storage_provider import S3StorageProvider, get_storage_provider
from src.infrastructure.storage_provider import LocalStorageProvider


def test_storage_provider_factory_selection():
    local_cfg = Settings(STORAGE_TYPE="local")
    prov_local = get_storage_provider(local_cfg)
    assert isinstance(prov_local, LocalStorageProvider)

    s3_cfg = Settings(
        STORAGE_TYPE="s3",
        S3_ENDPOINT_URL="http://localhost:9000",
        S3_BUCKET_NAME="test-bucket",
    )
    prov_s3 = get_storage_provider(s3_cfg)
    assert isinstance(prov_s3, S3StorageProvider)
    assert prov_s3.bucket_name == "test-bucket"


@pytest.mark.asyncio
async def test_s3_storage_provider_checksum_and_fallback():
    prov = S3StorageProvider(endpoint_url="http://invalid-local-host:9999", bucket_name="test-bucket")

    test_data = b"Hello, Autonomous Production World!"
    checksum = prov.compute_sha256(test_data)
    assert len(checksum) == 64  # SHA-256 hex string

    # Execute store (will use fallback seamlessly if endpoint is down)
    stored_ref = await prov.store_bytes("artifacts/test_file.txt", test_data)
    assert isinstance(stored_ref, str)

    # Execute read (will retrieve data correctly)
    read_data = await prov.read_bytes("artifacts/test_file.txt")
    assert read_data == test_data

    # Execute delete
    deleted = await prov.delete_bytes("artifacts/test_file.txt")
    assert deleted is True
