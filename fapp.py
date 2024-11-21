from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import logging
from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel, HttpUrl

class URLRequest(BaseModel):
    long_url: HttpUrl

class URLResponse(BaseModel):
    short_url: str
    long_url: str

async def initMongo():
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
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
    yield # give control to fastapi (fastapi handles requests while the app is running)
    await app.state.db.client.close() # code after yield runs on shutdown (of fastapi server)


app = FastAPI(lifespan=lifecycle)


# Configuration management
class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "url_shortener_db"
    COLLECTION_NAME: str = "url_collection"
    ALLOWED_ORIGINS: list = [
        "http://localhost:5000",
        "http://localhost:8000",
    ]
    
settings = Settings()   

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

# def initAsyncMongodb():
#     client = AsyncIOMotorClient('mongodb://localhost:27017')
#     db = client.url_shortener_db
#     collection = db.url_collection
#     return db, collection




    
# synchronous method    
def initMongoClient():
    db, collection = None, None
    try:
        mongo_client = MongoClient('mongodb://localhost:27017') # change as you deploy
        db:Database = mongo_client['url_shortener_db']
        collection: Collection = db['url_collection']
    except Exception as e:
        print(str(e))
        print('Exiting...')
        # exit()
    return db, collection


@app.get("/")
async def root():
    return {"message": "home route working"}

@app.get("/health")
async def health():
    return {"message": "healthy"}

@app.post("/api/encode")
async def encode():
    if app.state.db is None or app.state.collection is None:
        return {"message": "Cannot establish connection to MongoDB database"}
    else:
        
    


# 0.0.0.0 makes app accessible to any device on the network, otherwise 127.0.0.1 restricts to localhost
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5000)