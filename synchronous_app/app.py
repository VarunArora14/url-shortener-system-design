from random import randint, choices
from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from flask import redirect

app = Flask(__name__)

@app.route("/rolldice")
def roll_dice():
    return str(do_roll())

def do_roll():
    return randint(1, 6)
  
CORS(app=app) # allows cross origin access
chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

try:
  mongo_client = MongoClient('mongodb://localhost:27017')
  db:Database = mongo_client['url_shortener_db']
  collection: Collection = db['url_collection']
except Exception as e:
  print(e)
  print('Exiting...')
  exit()



@app.route("/api/test", methods = ['GET','POST'])
def test():
  if request.method == 'GET':
    return "hello world"

@app.route("/")
def home():
  return "working!"

@app.route("/api/encode", methods = ['POST'])
def encode():
  # get the long url from POST body
  data = request.json
  long_url = data["long_url"]
  
  # before creating new url, check if url already exists
  query = {"long_url": long_url}
  # check if any document exists with this
  try:
    if collection.count_documents(query)>0:
      print("long_url already exists in DB")
      documents = collection.find(query)
      for document in documents:
        short_url = document["short_url"]
        return {"short_url": short_url, "status": "existed"}
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
      
      collection.insert_one(new_doc) # added to the db
      print(f'Document inserted of long url {long_url}')
      return {"short_url": short_url, "status": "created"}
  except Exception as e:
    print(e)
    

@app.route("/<short_url>", methods=['GET'])
def decode(short_url):
  # get the url from body
#   data = request.json
#   short_url = data['short_url']
  url = "http://localhost:5000/" + short_url
  
  query = {"short_url": url}
  
  # it already exists, return from DB
  if collection.count_documents(query) > 0:
    print("short_url already exists in DB")
    documents = collection.find(query)
    for document in documents:
      long_url = document["long_url"]
    #   return {"status": "existed", "long_url": long_url}
      return redirect(long_url)
  else:
    # return info that long_url does not exist
    return {"status": "not_found", "long_url": ""}

if __name__ == '__main__':
  app.run(debug=False, port=8080)
  
  
# for requests, get data using request.json and get url params using request.args OR pass @app.route(<name>) and use same name inside method as func(name)
# to use the value if it does not have key in url like ?username=varun?age=21