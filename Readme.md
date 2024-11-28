The code is for implementing a url shortener service with **async** API calls being used as well as **synchronous** code implementation as part of `tiny_url.py`.

The aim is to implement and understand real world system design constraints and problems that we wish to solve.

In order to run the code via docker compose, run command `docker-compose up --build` to build the service and mongo container in same network.

For just running the app, run `python fapp.py`. Make sure than `IS_LOCAL` values is set to `True` in the `.env` file in the same folder directory as `fapp.py`
