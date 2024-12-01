### Testing Url Shortener Service

This project uses the **pytest** framework along with the **pytest-asyncio** plugin. The code -

```py
@pytest.fixture(scope="module")
async def test_app():
    app.dependency_overrides = {}
    # Using async with for proper handling of the AsyncClient instance
    async with AsyncClient(app=app, base_url="http://localhost:5000") as ac:
        yield ac  # Yield the client to the test
```

This sets up an instance of your app. It overrides existing connections or external APIs to clear test environments and creates a test Async client to simulate HTTP requests to the FastAPI app. The test client `ac` is then yielded to be used in test functions.

**Important** - Setting `scope="module"` in the `@pytest.fixture` ensures that the event loop remains active for all test cases within the module. Without this, the event loop may end prematurely, causing errors. Using `scope="session"` resulted in errors, but setting it to `scope="module"` resolved the issue by keeping the event loop active until all tests in the module are completed.

Note - The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

Then we create another fixture to setup DB for the app state -

```py
@pytest.fixture(scope="module")
async def setup_test_db():
    # Setup MongoDB and Redis for testing
    app.state.client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.state.db = app.state.client.test_db
    app.state.collection = app.state.db.test_collection
    app.state.redis = redis.from_url("redis://localhost:6379")
    yield
```

We define test cases via `@pytest.mark.anyio`.

We initialize the clients for each test (note that the fixtures themselves do not use **await**) and their implementation will consist of async-await methods.

```py
@pytest.mark.anyio
async def test_mong_redis(test_app, setup_test_db):
    mongodb_ping = await app.state.db.client.admin.command("ping")
    redis_ping = await app.state.redis.ping()
    assert mongodb_ping == {'ok': 1.0}
    assert redis_ping == True
```

The reason we changed `@pytest.mark.asyncio` to `@pytest.mark.anyio` was that in former the httpx app client as returning async_generator() and not the actual client.

Refer to other solution using `@pytest_asyncio.fixture` here - https://stackoverflow.com/questions/72996818/attributeerror-in-pytest-with-asyncio-after-include-code-in-fixtures

Also, with **anyio**, you can use other concurrency packages like **asyncio** and **trio** for tests and APIs.

The tests are added automatically based on `assert` in the code -

```py
assert response.status_code == 200
assert response.json() == {"message":"Home page"}
```

---

### Tests Hierarchy Issues

#### Current Hierarchy

```
project/
│
├── fapp.py
└── tests/
    └── test_fapp.py
```

To resolve import path issues when the `tests` folder needs to import `fapp.py` from the parent directory, add the following code:

```py
import sys
sys.path.append('../')
```

This modifies the python import path so python will look into that directory (parent in this case) when searching **modules** (fapp imported as module). This was done as the module or script is not in same folder but higher/lower in hierarchy
