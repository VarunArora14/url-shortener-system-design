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
