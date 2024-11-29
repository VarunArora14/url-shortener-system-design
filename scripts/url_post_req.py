# Here we generate urls and make a post request to the fastapi server to generate urls and store them in the database.
import requests
from random import randint
url = "http://localhost:5000/api/encode"

chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def generate_random_long_url():
    suffix=""
    for _ in range(7):
        r = randint(0, len(chars)-1)
        suffix+=chars[r]
    return f"http://example.com/{suffix}"

for i in range(10):
    print(i)
    long_url = generate_random_long_url()
    print(long_url)
    response = requests.post(url, json={"long_url": long_url})
    if response.status_code !=200:
        print(f"Failed to generate short url for {long_url}")
    