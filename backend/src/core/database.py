# from typing import AsyncGenerator
# from sqlalchemy import create_async_engine
# from sqlalchemy.orm import sessionmaker, DeclarativeBase
# from sqlalchemy.ext.declarative import declarative_base
# from .config import settings

# database_url = settings.DATABASE_URL

# engine = create_async_engine(database_url)

# session_local = sessionmaker(autocommit = False, autoflush=False, bind=engine)

# Base = declarative_base()

# class Base(DeclarativeBase):
#     pass

# async def get_db():
#     db = session_local()
#     try:
#         yield db
#     finally:
#         db.close()

# app/core/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()