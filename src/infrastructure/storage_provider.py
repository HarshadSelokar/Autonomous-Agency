"""
StorageProvider Interface and LocalStorageProvider implementation for Phase 7 Artifacts.
Decouples binary payload storage from PostgreSQL metadata persistence.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class StorageProviderInterface(ABC):
    """Abstract interface for storing and retrieving binary artifact payloads."""

    @abstractmethod
    async def store_bytes(self, key: str, data: bytes) -> str:
        """Store bytes under key and return storage key identifier."""
        pass

    @abstractmethod
    async def read_bytes(self, key: str) -> bytes:
        """Read bytes stored under key."""
        pass

    @abstractmethod
    async def delete_bytes(self, key: str) -> bool:
        """Delete stored payload by key."""
        pass


class LocalStorageProvider(StorageProviderInterface):
    """Local filesystem storage provider for artifact payloads."""

    def __init__(self, base_dir: str = "scratch/artifact_storage") -> None:
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def store_bytes(self, key: str, data: bytes) -> str:
        safe_key = key.replace("/", "_").replace("\\", "_")
        file_path = self.base_path / safe_key
        file_path.write_bytes(data)
        return str(file_path.absolute())

    async def read_bytes(self, key: str) -> bytes:
        file_path = Path(key)
        if not file_path.is_absolute() or not file_path.exists():
            safe_key = key.replace("/", "_").replace("\\", "_")
            file_path = self.base_path / safe_key
        if not file_path.exists():
            raise FileNotFoundError(f"Storage key '{key}' not found at {file_path}")
        return file_path.read_bytes()

    async def delete_bytes(self, key: str) -> bool:
        file_path = Path(key)
        if not file_path.is_absolute() or not file_path.exists():
            safe_key = key.replace("/", "_").replace("\\", "_")
            file_path = self.base_path / safe_key
        if file_path.exists():
            file_path.unlink()
            return True
        return False
