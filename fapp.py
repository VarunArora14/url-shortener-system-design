import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel, HttpUrl
from random import randint
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import redis.asyncio as redis


'''
References for implementation in FastAPI: 

https://fastapi.tiangolo.com/advanced/events/#lifespan
https://docs.pydantic.dev/latest/concepts/pydantic_settings/

'''

load_dotenv()


class URLRequest(BaseModel):
    long_url: HttpUrl

class URLResponse(BaseModel):
    short_url: Optional[str]=None   
    long_url: str
    error_message:Optional[str]=None


async def async_get_redis_client():
    try:
        client = await redis.Redis(host=settings.REDIS_LOCAL_HOST if settings.IS_LOCAL else settings.REDIS_CONTAINER_HOST, port=settings.REDIS_PORT, decode_responses=True)
        # Test the connection
        await client.ping()
        print("Connected to Redis!")
        return client
    except redis.RedisError as e:
        print(f"Redis connection error: {e}")

async def initMongo()-> Tuple[AsyncIOMotorDatabase, AsyncIOMotorCollection]:
    try:
        client = AsyncIOMotorClient(settings.MONGODB_LOCAL_URL) if settings.IS_LOCAL else AsyncIOMotorClient(settings.MONGODB_CONTAINER_URL)
        db = client[settings.DATABASE_NAME]
        collection = db[settings.COLLECTION_NAME]
        
        # verify connection
        await client.admin.command('ping')
        logger.info("Connected to mongDB")
        return db, collection
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        return None, None


@asynccontextmanager
async def lifecycle(app: FastAPI):
    app.state.db, app.state.collection = await initMongo() # code before yield runs on startup
    app.state.redis = await async_get_redis_client()
    yield # give control to fastapi (fastapi handles requests while the app is running)
    await app.state.db.client.close() # code after yield runs on shutdown (of fastapi server)
    await app.state.redis.close()


app = FastAPI(lifespan=lifecycle)


# Configuration management
class Settings(BaseSettings):
    MONGODB_LOCAL_URL: str = "mongodb://localhost:27017"
    MONGODB_CONTAINER_URL: str = "mongodb://mongo:27017"
    REDIS_LOCAL_HOST: str = "localhost"
    REDIS_CONTAINER_HOST: str = "redis"
    REDIS_PORT: int = 6379
    DATABASE_NAME: str = "url_shortener_db"
    LOCAL_APP_HOST: str = "localhost"
    CONTAINER_APP_HOST: str = "0.0.0.0"
    IS_LOCAL: bool = True
    COLLECTION_NAME: str = "url_collection"
    ALLOWED_ORIGINS: list = [
        "http://localhost:5000",
        "http://localhost:8000",
    ]
    class Config:
        # Allow the environment variables to override the settings in the class
        env_file = ".env"
        env_file_encoding = "utf-8"
    
settings = Settings() 
settings.IS_LOCAL = os.getenv("IS_LOCAL", "True").lower() == "true" 
print(settings.IS_LOCAL)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


    
# allow cors for these below urls
origins = [
    "http://localhost:5000",
    "http://localhost:8000",
    # Add more origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    

@app.get("/")
async def root():
    return {"message": "Home page"}

@app.get("/health")
async def health():
    redis_status = "OK"
    mongo_status = "OK"
    try:
        await app.state.db.command("ping")
    except Exception as e:
        mongo_status=str(e)
    try:
        await app.state.redis.ping()
    except Exception as e:
        redis_status=str(e)
        
    return {"status": "OK", "MongoDB Connection": mongo_status, "Redis Connection": redis_status}

@app.post("/api/encode", response_model=URLResponse)
async def encode(request: URLRequest):
    if app.state.db is None or app.state.collection is None:
        return URLResponse(long_url=request.long_url, error_message="Cannot establish connection to MongoDB database")
    else:
        long_url = str(request.long_url)
        logger.info(f"Received long url: {long_url}")
        query = {"long_url": long_url}
        try:
            count  = await app.state.collection.count_documents(query)
            if count>0:
                logger.info(f"Long url already exists in DB")
                document = await app.state.collection.find_one(query)
                short_url = document["short_url"]
                return URLResponse(short_url=short_url, long_url=long_url)
            else:
                suffix=""
                short_url = ""
                isValidShortUrl = False
                max_retries=10
                while not isValidShortUrl and max_retries>0:
                    for _ in range(7):
                        r = randint(0, len(chars)-1)
                        suffix+=chars[r]
                    
                    short_url = "http://localhost:5000/" + suffix
                    check_query = {"short_url": short_url}
                    count = await app.state.collection.count_documents(check_query)
                    if count==0:
                        isValidShortUrl = True
                    else:
                        print(f"Short url already exists for {long_url}. Generating a new one...")
                    max_retries-=1
                
                if max_retries==0:
                    raise Exception("Could not generate a unique short url after 10 retries")
                # insert a new document
                new_doc = {}
                new_doc["long_url"] = long_url
                new_doc["short_url"] = short_url
                
                await app.state.collection.insert_one(new_doc) # added to the db
                logger.info(f'Document inserted of long url {long_url}')
                return URLResponse(short_url=short_url, long_url=long_url)
        except Exception as e:
            return URLResponse(long_url=long_url, error_message=str(e))

@app.get("/{short_code}")
async def decode(short_code: str):
    short_url = f"http://localhost:5000/{short_code}"
    query = {"short_url": f"http://localhost:5000/{short_code}"}
    try:
        # add redis check here
        long_url = await app.state.redis.get(short_url)
        if long_url is not None:
            return RedirectResponse(url=long_url)
        else:
            print("cache miss")
            document = await app.state.collection.find_one(query)
            if document is not None:
                long_url = document["long_url"]
                await app.state.redis.set(short_url, long_url) # add key-value pair to redis
                return RedirectResponse(url=long_url)
            else:
                return {"message": "No such short url found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/urls")
async def list_urls():
    """
    Retrieve all documents from the MongoDB collection.
    """
    try:
        cursor = app.state.collection.find({}, {"_id": 0})
        documents = await cursor.to_list(length=1000)
        if documents == []:
            return {"message": "Empty collection"}
        elif documents is None:
            return {"message": "Collection not found"}
        else:
            return {"documents": documents}
    except Exception as e:
        return {"message": str(e)}


@app.get("/api/redis/list")
async def get_all_redis_pairs(batch_size: int = 500):
    """
    Retrieve all key-value pairs from Redis in batches.

    Args:
        batch_size (int): The number of keys to retrieve in each batch. Default is 500.

    Returns:
        dict: A dictionary containing all key-value pairs from Redis.
    """
    pairs = {}
    try:
        async for key in app.state.redis.scan_iter(match="*", count=batch_size):
            value = await app.state.redis.get(key)
            pairs[key] = value
        return pairs
    except redis.RedisError as e:
        return {"Redis error": str(e)}
    except Exception as e:
        return {"error": str(e)}
    


# 0.0.0.0 makes app accessible to any device on the network, otherwise 127.0.0.1 restricts to localhost
if __name__ == "__main__":
    host = settings.LOCAL_APP_HOST if settings.IS_LOCAL else settings.CONTAINER_APP_HOST
    # put 0.0.0.0 for docker
    uvicorn.run("fapp:app", host=host, port=5000, reload=True) # reload=True for auto-reload on code changes
    # passed "fapp:app" as reload=True expects this format and "fapp" is the name of the file/module