import asyncio
import sys
import os

# Set Python path to include current directory
sys.path.append(os.getcwd())

from app.db import async_session
from app.db.models import User
from sqlalchemy import select

async def check_users():
    async with async_session() as session:
        res = await session.execute(select(User))
        users = res.scalars().all()
        for u in users:
            print(f"ID: {u.id}, Name: {u.full_name}, Username: {u.username}")

if __name__ == "__main__":
    asyncio.run(check_users())
