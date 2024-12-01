- The current `fapp.py` will be used as the main application which will be having a custom error page in case the URL does not exist. Otherwise, it will redirect to the actual website which for which the mapping was stored.
- The main thing will be what will be the url of the application deployed which we will see after deployment.
- It needs a potential dashboard page for looking all the urls that exist in it or we can use some mongodb ui for that (better to create our own for other analytics). Logging will be important when analytics is enabled.
- Have proper error handling in it with input validation(prevent sqlite injection, xss attacks) and security (https for all urls?)
- Another functionaility will be deleting of the urls as they expire (24 hours as default time)
- Find ways to make it scalable and learn about caching and DB choices which can make this better in scalability with reasons
- have hashing algos for unique key generation
- index database for faster lookups
- cache popular urls in redis for low latency

### Enterprise grade features

- load balancing => distribute traffic across different servers for high availability
- searchable url database => find urls by tags or keywords
- monitoring and alerts(unusual traffic patterns) => have alerting system via mail, sms etc

### TODO

- make a ui over database for urls => ui or mongodb or mysql for looking at the urls
- decide which db better for this and how caching can be done based on count of hits? - DONE
- store the dates of url generated so you run crons to delete the 'marked deleted' urls and on fetching them, check the expiry as well
- deploy to docker compose first or directly k8s - DONE
- configure jenkinsfile for accordingly setup after the code is ready and working locally
- document everything including the learnings of choices of DB and code - DONE

---

### For dockerfile

We start with single docker file with lock mongoDB and redis and then we use docker compose with mongodb and redis in same docker network.
