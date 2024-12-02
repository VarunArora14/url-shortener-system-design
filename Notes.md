### Docker Workflow Diagram

![alt text](image.png)

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
- The code is run via command `uvicorn fapp:app --host 0.0.0.0 --port 5000` and not `python fapp.py` as when we run the latter command, the uvicorn server runs inside the python process which reduces our control if let's say we want to run it as servie with process manager like `systemd`. Running uvicorn server directly provides advanced server config options and **avoids overhead of running it through python**. Running uvicorn app server is better for production ready servers to be deployed than python scripts.

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
  Refer to redis-py documentation for more asyncio - https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html
- **Interesting finding** - If a docker container with app is running at localhost port 5000 and you run `python fapp.py` again then it will set the db client objects as None despite giving message "Connected to MongoDB". And if you run the code via **uvicorn** then it runs just fine. To solve this, stop the existing docker container and run `python fapp.py`

### Potential Improvements to implementation

- The `created_date`, `expiration_date` can be added to service to make the service handle expiries of urls.
- The random short url generation can be replaced with KGS (Key Generation Service) which offline prepares a database of keys which are then used to create these short urls by taking that key. For concurrency, once key is taken, it should be marked to not be used. For multiple server scenarios, it can have 2 DBs (used and unused keys) and can transfer the key from used to unused as soon as the service gives key to one of the app servers. For a 6 character short code, the DB size will be `6 x 68.7B = 412 GB`.
- We wil also need KGS in a cluster so if master fails then the replica becomes master as a standby/read replica is needed in case of failover.
- We need to decide the cache size for redis, this can be around 20% of the daily traffic (assuming 80% of the traffic is by 20% of the urls) . Also, LRU key eviction strategy as used now should be decent.
- We need LB for client to application server, application server to mongoDB, application server to redis. This can be easily done with setting them in cluster config in k8s and use round robin as default load balancing algo.
- For purging or cleaning the expired urls, we can have functioanlity that if user clicks on expired url(having existing mapping in DB but expired) we return error of expiry and mark it expired (flag as part of db object or simply delete it). If we have a flag then we can run crons every x hours to delete all expired urls `current_time > expiry_time`. This handles cases when urls are expired but no one accesses them for a very long time without getting hits taking increasing space in DB.

### Ideal URL Shortener System Design

![alt text](url-shortener-design.png)

---

## Deploying to local Kubernetes

I will use **minikube** to create deployments with service and ingress. For ingress, we generally provide **host** which should be same as the DNS mapping in the DNS server (like Route53 on AWS cloud). Since we are not deploying right now to cloud, we pass the DNS name we want for our url shortener service for which we have to modify our **local hosts file** in **/etc/hosts** and NOT use the minikube IP. Follow the forum for entire steps - https://stackoverflow.com/questions/58561682/minikube-with-ingress-example-not-working

#### Upload Local Docker Image to Dockerhub

- Firstly upload your local docker image to format `<dockerhub_username>/<image_name>:<tag>` like `docker image tag url_shortener-app rdxdocker14/url-shortener-app` (here the default tag used was latest).
- Push docker image to docker hub - `docker image push rdxdocker14/url-shortener-app`

### Run MongoDB via yaml files in single pods

Run the file `k8s/mongodb.yml` and then set the pod name as **mongo** (for the connection url `mongodb://mongo:27017`). To check the internal dns mapping, we can run busybox and confirm the DNS mappings of a **service** of kubernetes.

Run command `kubectl run -it --rm busybox --image=busybox:1.28` and then inside the busybox, run command `nslookup <service_name>` which here is `nslookup mongo` and we get the FQDN **mongo.default.svc.cluster.local**

Note - The `REDIS_PORT` variable being int was somehow being represented as `tcp://<internal_ip>:6379` as it's value and on commenting it and passing the actual **redis url** with `redis.from_url(...)` solved the issue. It is important to give **new tag** to each docker image to avoid having same code in docker image (cached) to be used.

### Deployment to Kubernetes

- In order to deploy the app to kubernetes, we need to setup the databases first. For this we create files **mongodb.yml** and **redis.yml** and run command `kubectl apply -f <filename.yml>` to create those services respectively. These are services with single pods behind them as databases.
- Once these databases are tried and tested for connection, we can make changes in our code to mention new urls for internal communication in kubernetes which happens to be FQDN of these services in format `<service_name>.<namespace>.svc.cluster.local:<port_number>` like `mongo.default.svc.cluster.local:27017`.
- These can be tested via `nslookup <service_name>` command with a busybox container to confirm DNS mapping.
- After this, I create new urls for mongo and redis connection based on their FQDN.
- Build docker image from code and then upload it to dockerhub in public repo after proper tagging
- Create a file named `k8s/app.yml` which contains the configuration of **pod**, **service** and **ingress** respectively
- I deploy this on **minikube** windows as per documentation here - https://minikube.sigs.k8s.io/docs/
- Run commands in terminal `minikube addons enable ingress-dns` and `minikube addons enable ingress` for DNS resolution locally
- Apply the app yml file via `kubectl apply -f app.yml` and then check pods and logs of these containers if the app has successfully run
- Run command `minikube tunnel` to access it via localhost. If it does not do DNS resolution by any reason, instead **port forward the app service to port you want** via `kubectl port-forward svc/<service_name> <host_port>:<service_port>` leading to `kubectl port-forward svc/url-shortener 5000:5000`
- Check the functionality to be same as it worked in locally with all APIs working as expected

Note - On deploying services, **ClusterIP** is the **default type** and you can change this to **NodePort** or **LoadBalancer** as well.

### Next Steps

- Replicaset for **mongodb** and **redis**
- Jenkins CI/CD deployment instead of building and deploying docker images manually
- Add cpu and memory limits to each **deployment** yaml - DONE
- Adding **Persistent Volumes** and **PVC** to mongodb and redis for persistence - DONE
