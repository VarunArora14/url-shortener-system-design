FROM python:3.11.0-slim

# set current working directory
WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# RUN apt-get -y update; apt-get -y install curl

COPY fapp.py /app/

# COPY .env /app/

EXPOSE 5000

ENV LOCAL=False

CMD ["uvicorn", "fapp:app", "--host", "0.0.0.0", "--port", "5000"]

# command ---no-cache  docker build -t url-shortener .