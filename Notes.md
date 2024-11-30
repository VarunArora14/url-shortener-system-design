The code is for implementing a url shortener service with **async** API calls being used as well as **synchronous** code implementation as part of `synchronous_app/app.py`.

The aim of this project is to implement and understand real world system design constraints and problems that we wish to solve.

In order to run the code via docker compose, run command `docker-compose up --build` to build the service and mongo container in same network.

For just running the app, run `python fapp.py`. Make sure than `IS_LOCAL` values is set to `True` in the `.env` file in the same folder directory as `fapp.py`

Important API endpoints:

- `/` - returns home page json
- `/health` - health check of API and database
- `/api/encode` - Post endpoint expecting data in format `{long_url: 'url'}`
- `/{short_code}` - Redirects the existing site to the mapped url as in database.
- `/api/list` - List all the url mappings of long to short urls
- `/docs` - Swagger documentation of above APIs

The way it works is that if my base url is `http://localhost:5000`, then I save the short url in format `http://localhost:5000/{short_code}` which then handles the routing to the actual mapped url.

System Design Choices -

- **MongoDB** has been used as database to store long-short url mappings as it **scales out** via **horizontal scaling** and is much more resilient than SQL based databases especially during **high throughput**(NoSQL has much higher throughput while SQL has transactional accuracy). SQL databases will enncounter performance issues for large amount of data (non transactional) especially if need horizontal scaling. Vertical scaling will be much **more expensive** for large scale. Another reason is **high availability** of NoSQL databases via data replication and fault toleration via master-slave node cluster setup.
- **Redis** is a great choice for storing most common urls as it can avoid DB searches for mappings of short urls. LRU or some other **key eviction policy** must be set with proper cluster/standalone config for cache eviction.
- **FastAPI** as application server has been used to handle async requests with respective async libraries being used for handling large number of requests. This will be then deployed on k8s with with multiple instances (load balanced with `service` using round robin)

Other Implementation choices -

- Use of **random code generator** over **hash + base64 encode** of url for short url creation has been done as if we use hash with encoding, while we get a unique id for each url, collision resolution for this won't be easy. It is better to generate random urls => check their occurence and then store them.
- In redis fetch of all key-value pairs as part of API, I used `scan()` method and not `keys()` method as for a larger number of key-val pairs, the method blocks the server while the `scan()` method brings pagination giving few results at a time maintaining cursor position as well. Note that **cursor** is index to the iterator which scan command updates for subsequent calls (same as next page for pagination). The `scan` method works with user initialising `cursor` to 0 and ends when the server returns a cursor of 0. It works by updating cursor with each call and return to user for next iteration step. We use `scan_iter` abstraction by redis-py package that **abstratcs away cursor management and directly provides python iterator** for easier loops. This method is superior to `KEYS` which has blocking code and blocks IO operations till the processing is complete.
- The DB connections for redis and mongoDB are stored inside the **fastapi app state** as part of best practice providing **async context manager** for managing lifecycle of FastAPI app. This context manager allows to manage resources that need to be setup before the application starts and cleaned up after the application stops.

Redis `scan_iter implementation` -

```py
pairs = {}
try:
    # provide proper match and batch size as small batch size means slow execution as all batch keys come at a time with cursor managed by redis-py. this method has to be async
    async for key in app.state.redis.scan_iter(match="*", count=batch_size):
        value = await app.state.redis.get(key)
        pairs[key] = value
    return pairs
except redis.RedisError as e:
    return {"Redis error": str(e)}
except Exception as e:
    return {"error": str(e)}
```

Redis commands -

- Inside redis docker container run command `redis-cli` to connect
- Run command `ping` to confirm
- Command `keys *` to get all keys
- command `get <keyname>` to get the corresponding value of the `<keyname>`
- command `set <k> <v>` to set key-value pairs

Additional things found as part of learning -

- Run command `fastapi dev <app.py>` for running dev server when **uvicorn** server is not used
- If uvicorn is being used, provide the name of the file which represents the app as `uvicorn.run("myapp:app",..)` where `myapp` is the `myapp.py` containing your code
- If you have made code changes and your uvicorn server is not having those changes, go to your task manager or do `ls`(for linux) and find programs whose name have `python.exe` in them and do **end task** on them. For linux, kill their task PID by `taskkill /PID <PID> /F` (force kill pid)
- If you have **MongoDB** running both locally and on docker at same port **27017** and have docker port exposed to same port as well, then if you make request to `127.0.0.1:27017` then the request will go to the **local DB** and NOT the docker container. In docker-compose in windows, it uses docker internal network for requests. For internal networking, the host url changes from **mongodb://localhost:27017** to **mongodb://mongo:27017** (mongo is the container name and so this host). Note - this is without the credentials which should be configured as well. For accessing the **container mongodb** from outside, change the **host-container** port mapping as `m-compose.yml` file.
- For making requests to other containers running in same docker internal network, use their **container name as the hostname for automatic DNS resolution for container names**. If the container name is **mongo2** then conn url is `mongodb://mongo2:27017`. Similarly, if for redis the container name is **redis**, then it's conn url is `redis://redis:6379/0`. Refer to the format - `redis://[:password]@host:port[/db_number]`. For local redis, it will be `redis://localhost:6379/0`.
