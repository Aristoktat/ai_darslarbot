from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime, ForeignKey, MetaData, LargeBinary, select
from datetime import datetime
from app.config import settings
import asyncio
from app.db import init_db

# Reuse models from app.db.models
from app.db.models import Plan, async_session

async def seed_data():
    await init_db()
    async with async_session() as session:
        # Check if plans exist
        result = await session.execute(select(Plan))
        existing_plans = result.scalars().all()
        
        if not existing_plans:
            print("Creating default plans...")
            plans = [
                Plan(name="1 Oylik", duration_days=30, price=9900000, is_active=True), # 99,000.00
                Plan(name="3 Oylik", duration_days=90, price=24900000, is_active=True), # 249,000.00
                Plan(name="Lifetime", duration_days=None, price=59900000, is_active=True) # 599,000.00
            ]
            session.add_all(plans)
            await session.commit()
            print("Plans created!")
        else:
            print("Plans already exist.")

if __name__ == "__main__":
    asyncio.run(seed_data())
