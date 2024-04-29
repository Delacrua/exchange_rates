FROM python:3.12

RUN apt update && apt -y install gettext-base

COPY requirements.txt .

RUN pip install -r requirements.txt

WORKDIR /app

ADD . /app

EXPOSE 8888