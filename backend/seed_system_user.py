import asyncio
from sqlalchemy import select
from app.models import User
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(__file__))
from app.database import AsyncSessionLocal

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

async def seed():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == SYSTEM_USER_ID))
        if result.scalar_one_or_none():
            print("System user already exists.")
            return
        system_user = User(
            id=SYSTEM_USER_ID,
            username="arcanum_system",
            email="system@arcanum.internal",
            hashed_password="SYSTEM_ACCOUNT_NO_LOGIN",
            is_active=False,  # Can never log in
        )
        db.add(system_user)
        await db.commit()
        print(f"System user created: {SYSTEM_USER_ID}")

if __name__ == "__main__":
    asyncio.run(seed())