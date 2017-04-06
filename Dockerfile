FROM      ubuntu:16.04
MAINTAINER DAIDV <daikk115@gmail.com>

RUN apt-get update && apt-get install -y  \
    python3 \
    python3-pip

RUN pip3 install aiohttp==0.17.4 \
    python-swiftclient \
    python-keystoneclient \
    keystoneauth1

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY wrapper/ /wrapper/

WORKDIR /wrapper/
RUN chmod +x service.py
CMD ./service.py -i 0.0.0.0 -p 8080
#CMD python3 service.py

EXPOSE 8080
