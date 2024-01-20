FROM python:3.11

ENV PYTHONUNBUFFERED 1

RUN mkdir /statistics
WORKDIR /statistics

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
