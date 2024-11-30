The code is for implementing a url shortener service with **async** API calls being used as well as **synchronous** code implementation as part of `tiny_url.py`.

The aim is to implement and understand real world system design constraints and problems that we wish to solve.

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

Redis commands -

- Inside redis docker container run command `redis-cli` to connect
- Run command `ping` to confirm
- Command `keys *` to get all keys
- command `get <keyname>` to get the corresponding value of the `<keyname>`
- command `set <k> <v>` to set key-value pairs
