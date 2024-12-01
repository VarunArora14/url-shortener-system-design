import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import sys
sys.path.append('../')
from fapp import app, lifecycle

# pytestmark = pytest.mark.anyio

@pytest.fixture(scope="module")
async def test_app():
    app.dependency_overrides = {}
    # Using async with for proper handling of the AsyncClient instance
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:5000") as ac:
        yield ac  # Yield the client to the test

@pytest.fixture(scope="module")
async def setup_test_db():
    # Setup MongoDB and Redis for testing
    app.state.client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.state.db = app.state.client.test_db
    app.state.collection = app.state.db.test_collection
    app.state.redis = redis.from_url("redis://localhost:6379")
    yield
    await app.state.redis.aclose() # async as it requires network calls and closing socket connections
    app.state.client.close() # close method is synchornous for motor client

@pytest.mark.anyio
async def test_mong_redis(test_app, setup_test_db):
    mongodb_ping = await app.state.db.client.admin.command("ping")
    redis_ping = await app.state.redis.ping()
    assert mongodb_ping == {'ok': 1.0}
    assert redis_ping == True

@pytest.mark.anyio
async def test_root_endpoint(test_app, setup_test_db):
    print(type(test_app))
    response = await test_app.get("/")
    assert response.status_code == 200
    assert response.json() == {"message":"Home page"}

@pytest.mark.anyio
async def test_set_and_get_url(test_app, setup_test_db):
    long_url = "https://www.example.com"
    response = await test_app.post("/api/encode", json={"long_url": long_url})
    print(response.json())
    assert response.status_code == 200
    short_url = response.json()["short_url"]
    print("short_url", short_url)

    response = await test_app.get(f"/{short_url.split('/')[-1]}")
    assert response.status_code == 307 # redirect status code

@pytest.mark.anyio
async def test_get_non_existing_url(test_app, setup_test_db):
    response = await test_app.get("/nonexisting")
    assert response.status_code == 404
    assert response.json() == {"message": "No such short url found"}

# @pytest.mark.asyncio
# async def test_list_urls(test_app, setup_db):
#     response = await test_app.get("/api/urls")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Empty collection"}

#     long_url = "https://www.example.com"
#     await test_app.post("/shorten", json={"long_url": long_url})

#     response = await test_app.get("/api/urls")
#     assert response.status_code == 200
#     assert len(response.json()["documents"]) == 1
#     assert response.json()["documents"][0]["long_url"] == long_url