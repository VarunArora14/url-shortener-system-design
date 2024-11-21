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
from random import randint
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from fastapi.responses import RedirectResponse


'''
References for implementation in FastAPI: 

https://fastapi.tiangolo.com/advanced/events/#lifespan
https://docs.pydantic.dev/latest/concepts/pydantic_settings/

'''


class URLRequest(BaseModel):
    long_url: HttpUrl

class URLResponse(BaseModel):
    short_url: Optional[str]=None   
    long_url: str
    error_message:Optional[str]=None


# c = URLRequest(long_url="https://www.google.com") # make sure to provide 'long_url=' else error
# print(c.long_url)
# print(str(c.long_url))

async def initMongo()-> Tuple[AsyncIOMotorDatabase, AsyncIOMotorCollection]:
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
    return {"message": "Home page"}

@app.get("/health")
async def health():
    return {"message": "healthy"}

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
                short_url=""
                for _ in range(7):
                    r = randint(0, len(chars)-1) # get the random index
                    short_url+=chars[r]
                    
                short_url = "http://localhost:5000/" + short_url
                
                # insert a new document
                new_doc = {}
                new_doc["long_url"] = long_url
                new_doc["short_url"] = short_url
                
                await app.state.collection.insert_one(new_doc) # added to the db
                logger.info(f'Document inserted of long url {long_url}')
                return URLResponse(short_url=short_url, long_url=long_url)
        except Exception as e:
            return URLResponse(long_url=long_url, error_message=str(e))

@app.get("/{short_url}")
async def decode(short_url: str):
    query = {"short_url": f"http://localhost:5000/{short_url}"}
    try:
        document = await app.state.collection.find_one(query)
        if document is not None:
            long_url = document["long_url"]
            return RedirectResponse(url=long_url)
        else:
            return {"message": "No such short url found"}
    except Exception as e:
        return {"message": str(e)}

# 0.0.0.0 makes app accessible to any device on the network, otherwise 127.0.0.1 restricts to localhost
if __name__ == "__main__":
    uvicorn.run("fapp:app", host="localhost", port=5000, reload=True) # reload=True for auto-reload on code changes
    # passed "fapp:app" as reload=True expects this format and "fapp" is the name of the file/module