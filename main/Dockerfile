FROM python:latest

ENV PYTHONNUNBUFFERED 1

WORKDIR /usr/src/app

COPY requirements.txt ./ 

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

