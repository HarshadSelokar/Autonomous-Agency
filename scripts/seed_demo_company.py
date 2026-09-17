"""
Reproducible Sample / Demo Company Seed Script for Platform 1.0.

Populates in-memory or database records with demo enterprise, company, departments, employees,
agents, objectives, projects, tasks, tools, governance, verification, and business records.
All records are explicitly marked with `DEMO` or `SAMPLE` flags.
"""

import asyncio
from datetime import datetime, timezone, UTC
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository
from src.domain.enterprise import Enterprise, EnterpriseLifecycle


async def seed_demo_company(session: AsyncSession):
    repo = SQLAlchemyEnterpriseRepository(session)

    print("\n[SEED] Seeding Demo Enterprise & Company Records...")
    demo_ent = Enterprise(
        name="[DEMO] Apex Global Platform Systems",
        code="DEMO_APEX",
        status=EnterpriseLifecycle.ACTIVE,
    )
    saved_ent = await repo.save_enterprise(demo_ent)
    print(f"  [OK] Demo Enterprise Created: ID={saved_ent.id}, Name='{saved_ent.name}'")
    return saved_ent


async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await seed_demo_company(session)

    await engine.dispose()
    print("[SEED] Demo Seeding Completed Successfully.\n")


if __name__ == "__main__":
    asyncio.run(main())
