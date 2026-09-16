"""Unit test for automated database backup and restore tools."""

import pytest
from scripts.backup_database import run_backup
from scripts.restore_database import run_restore


@pytest.mark.asyncio
async def test_backup_and_restore_flow():
    db_url = "sqlite+aiosqlite:///:memory:"
    backup_result = await run_backup(db_url=db_url)

    assert "backup_key" in backup_result
    assert "checksum" in backup_result
    assert len(backup_result["checksum"]) == 64

    # Test restore from created backup key
    restore_success = await run_restore(backup_result["backup_key"], db_url=db_url)
    assert restore_success is True
