# syntax=docker/dockerfile:1

FROM --platform=linux/amd64 python:3.11.5

WORKDIR /app

ADD app app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

CMD [ "python", "-m", "streamlit", "run", "app/main.py" ]
