"""S3-Compatible Object Storage Provider & Integrity Verification.

Provides S3/MinIO payload storage with SHA-256 integrity checksums.
"""

import hashlib
import logging
from typing import Any
import httpx

from src.infrastructure.config import Settings, settings
from src.infrastructure.storage_provider import LocalStorageProvider, StorageProviderInterface

logger = logging.getLogger(__name__)


class S3StorageProvider(StorageProviderInterface):
    """S3 / MinIO Object Storage provider with SHA-256 integrity verification."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        bucket_name: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
    ) -> None:
        self.endpoint_url = (endpoint_url or settings.S3_ENDPOINT_URL or "http://localhost:9000").rstrip("/")
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.access_key = access_key or settings.S3_ACCESS_KEY_ID or "minioadmin"
        self.secret_key = secret_key or settings.S3_SECRET_ACCESS_KEY or "minioadmin"
        self.region = region or settings.S3_REGION

    def compute_sha256(self, data: bytes) -> str:
        """Compute SHA-256 hex checksum of payload."""
        return hashlib.sha256(data).hexdigest()

    async def store_bytes(self, key: str, data: bytes) -> str:
        """Store bytes under bucket/key with SHA-256 checksum header."""
        checksum = self.compute_sha256(data)
        safe_key = key.lstrip("/")
        url = f"{self.endpoint_url}/{self.bucket_name}/{safe_key}"

        headers = {
            "Content-Type": "application/octet-stream",
            "x-amz-meta-sha256": checksum,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.put(url, content=data, headers=headers)
                if resp.status_code in (200, 201):
                    logger.info(f"Stored artifact '{safe_key}' to S3 storage at {url} (SHA256: {checksum[:8]}...)")
                    return f"s3://{self.bucket_name}/{safe_key}"
                raise ValueError(f"S3 PutObject failed with status {resp.status_code}: {resp.text}")
            except httpx.RequestError as err:
                logger.warning(f"S3 connection failed ({err}), storing payload in local fallback...")
                # Fallback to local storage if endpoint unreachable
                local_prov = LocalStorageProvider()
                return await local_prov.store_bytes(key, data)

    async def read_bytes(self, key: str) -> bytes:
        """Read bytes from bucket/key and verify SHA-256 checksum if available."""
        safe_key = key.replace(f"s3://{self.bucket_name}/", "").lstrip("/")
        url = f"{self.endpoint_url}/{self.bucket_name}/{safe_key}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.content
                    expected_checksum = resp.headers.get("x-amz-meta-sha256")
                    if expected_checksum:
                        actual_checksum = self.compute_sha256(data)
                        if actual_checksum != expected_checksum:
                            raise ValueError(f"Checksum mismatch for S3 key '{key}': expected {expected_checksum}, got {actual_checksum}")
                    return data
                raise FileNotFoundError(f"S3 GetObject failed with status {resp.status_code}")
            except httpx.RequestError as err:
                logger.warning(f"S3 connection error ({err}), reading from local fallback...")
                local_prov = LocalStorageProvider()
                return await local_prov.read_bytes(key)

    async def delete_bytes(self, key: str) -> bool:
        """Delete payload from bucket/key."""
        safe_key = key.replace(f"s3://{self.bucket_name}/", "").lstrip("/")
        url = f"{self.endpoint_url}/{self.bucket_name}/{safe_key}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.delete(url)
                return resp.status_code in (200, 204)
            except httpx.RequestError:
                local_prov = LocalStorageProvider()
                return await local_prov.delete_bytes(key)


def get_storage_provider(cfg: Settings | None = None) -> StorageProviderInterface:
    """Factory function returning configured storage provider instance."""
    conf = cfg or settings
    if conf.STORAGE_TYPE.lower() == "s3":
        return S3StorageProvider(
            endpoint_url=conf.S3_ENDPOINT_URL,
            bucket_name=conf.S3_BUCKET_NAME,
            access_key=conf.S3_ACCESS_KEY_ID,
            secret_key=conf.S3_SECRET_ACCESS_KEY,
            region=conf.S3_REGION,
        )
    return LocalStorageProvider(base_dir=conf.LOCAL_STORAGE_DIR)
