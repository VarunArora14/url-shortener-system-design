FROM python:3.11.0-slim

# set current working directory
WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get -y update; apt-get -y install curl

COPY fapp.py /app/

COPY .env /app/

EXPOSE 5000

CMD ["python", "fapp.py"]

# command - docker build -t url-shortener .