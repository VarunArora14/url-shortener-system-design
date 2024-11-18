import random

chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


long_to_short_dict = {}
short_to_long_dict = {}

def choices_encode(long_url: str):
  # generate the short code of len 6
  while long_url not in long_to_short_dict:
    new_url_code = "".join(random.choices(chars, k=6)) # len is 6
    if new_url_code not in short_to_long_dict:
      long_to_short_dict[long_url]=new_url_code
      short_to_long_dict[new_url_code] = long_url
  
  return 'http://tinyurl.com/' + long_to_short_dict[long_url]

  
  
def decode(short_url:str):
  url_code = short_url[-6:]
  return short_to_long_dict[url_code] # the code is the key and value is the long url

def random_encode():
  res=""
  for i in range(7):
    r = random.randint(0,len(chars)-1)
    res+=chars[r]
  
  
  print(f"test url is http://tinyurl.com/{res}")

# print(encode("http://yolo.com/id=12312?major=24"))
random_encode()