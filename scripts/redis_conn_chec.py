from fastapi import FastAPI, Depends
import redis

app = FastAPI()

# Initialize Redis client
def get_redis_client():
    try:
        client = redis.Redis(host="localhost", port=6379, decode_responses=True) # decode responses as bytes string as answer
        # Test the connection
        if client.ping():
            print("Connected to Redis!")
        return client
    except redis.ConnectionError as e:
        print(f"Redis connection error: {e}") 
        

# Dependency to inject Redis client
def redis_dependency():
    return get_redis_client()

@app.get("/")
def read_root(redis_client=Depends(redis_dependency)):
    redis_client.set("message", "Hello, Redis!")
    return {"message": redis_client.get("message")}

@app.get("/set/{key}/{value}")
def set_key(key: str, value: str, redis_client=Depends(redis_dependency)):
    redis_client.set(key, value)
    return {"key": key, "value": value}

@app.get("/get/{key}")
def get_key(key: str, redis_client=Depends(redis_dependency)):
    value = redis_client.get(key)
    if value is None:
        return {"error": f"Key '{key}' not found"}
    return {"key": key, "value": value}

# TODO: test above code


import hashlib
import base64

def generate_short_url(original_url: str) -> str:
    # Create a SHA-256 hash of the original URL
    hash_object = hashlib.sha256(original_url.encode())
    # Encode the hash in base64 to make it shorter
    base64_encoded = base64.urlsafe_b64encode(hash_object.digest())
    # Take the first 8 characters to create a short URL
    short_url = base64_encoded[:8].decode('utf-8')
    return short_url

# Example usage
original_url = "https://www.example.com/some/long/url"
short_url = generate_short_url(original_url)
print(f"Original URL: {original_url}")
print(f"Short URL: {short_url}")
