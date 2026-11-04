from pathlib import Path

import pytest_asyncio
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from database import get_db
from main import app
from models.base import Base

import models.user
import models.movie
import models.review
import models.favorite
import models.follow
import models.message
import models.notification


ROOT_DIR = Path(__file__).resolve().parents[1]
env = dotenv_values(ROOT_DIR / ".env.test")

TEST_DATABASE_URL = env.get("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing")

if make_url(TEST_DATABASE_URL).database != "cinema_test":
    raise RuntimeError("Tests must use cinema_test database")


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        try:
            async with AsyncSession(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        async with AsyncSession(
            bind=db_session.bind,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
