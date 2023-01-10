FROM python:3.10
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  postgresql-client-13

COPY requirements/base.txt /code/
COPY requirements/local.txt /code/

RUN pip install -r local.txt

COPY . /code/
