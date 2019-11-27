FROM ubuntu:18.04

MAINTAINER Panos Ipeirotis "panos.ipeirotis@compass.com"

# Get the latest packages 
RUN apt-get -qy update
        

# Install Python
RUN apt-get  -qy install build-essential \
        python3-dev \
        python3-pip 

# Library for Postgres / RedSfhift
RUN apt-get -qy install libpq-dev

# Latest pip
RUN pip3 install -U pip

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -U -r requirements.txt

COPY . /app

WORKDIR /app

# Key is restricted to the Geocoding API and only to
# the two IP addresses 3.90.198.216 and 35.212.72.29
ENV GOOGLE_MAPS_KEY=AIzaSyDz90g6N1AeRb0n5foe1opZgoZq6scx660
ENV CENSUS_KEY=627d4107b57d4576f2120d2b87b59c7440e5d2af

EXPOSE 5000

ENTRYPOINT [ "python3"]

CMD [ "api.py" ]