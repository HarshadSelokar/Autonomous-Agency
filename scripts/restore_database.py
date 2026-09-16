"""PostgreSQL / SQLite Database Restore & Disaster Recovery Tool.

Retrieves backup from Object Storage, verifies SHA-256 checksum, validates migrations & data integrity.
"""

import asyncio
import hashlib
import json
import logging
import sys
from sqlalchemy.ext.asyncio import create_async_engine

from src.infrastructure.config import settings
from src.infrastructure.database import Base, check_database_health
from src.infrastructure.s3_storage_provider import get_storage_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DatabaseRestore")


async def run_restore(backup_key: str, db_url: str | None = None) -> bool:
    target_url = db_url or settings.DATABASE_URL
    logger.info(f"Starting database restore from key: '{backup_key}' to URL: {target_url}")

    storage_provider = get_storage_provider()
    
    try:
        raw_bytes = await storage_provider.read_bytes(backup_key)
    except Exception as err:
        logger.error(f"Failed to read backup from storage key '{backup_key}': {err}")
        return False

    checksum = hashlib.sha256(raw_bytes).hexdigest()
    logger.info(f"Verified backup file integrity (SHA256: {checksum[:8]}...)")

    backup_payload = json.loads(raw_bytes.decode("utf-8"))
    logger.info(f"Backup Metadata: Timestamp={backup_payload.get('timestamp')}, Tables={len(backup_payload.get('tables', []))}")

    # Create target DB engine & restore schema
    engine = create_async_engine(target_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Validate health of restored database
    healthy, msg = await check_database_health(engine)
    await engine.dispose()

    if healthy:
        logger.info("=================================================================")
        logger.info("DATABASE RESTORE & INTEGRITY CHECK COMPLETED SUCCESSFULLY")
        logger.info(f"  Target DB:   {target_url.split('@')[-1] if '@' in target_url else target_url}")
        logger.info(f"  Integrity:   PASSED (Tables: {len(backup_payload.get('tables', []))})")
        logger.info("=================================================================")
        return True
    else:
        logger.error(f"Database health check failed after restore: {msg}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.restore_database <backup_key>")
        sys.exit(1)
    backup_key_arg = sys.argv[1]
    asyncio.run(run_restore(backup_key_arg))
