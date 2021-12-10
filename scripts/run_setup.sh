#!/bin/sh

docker build -t axie-ronin-bot . && \
cp -u -p credentials.example.json credentials.json && \
cp -u -p config.example.json config.json && \
docker run \
  -it \
  --rm \
  --name axie-ronin-bot-setup \
  --mount type=bind,source="$(pwd)"/credentials.json,target=/usr/src/app/credentials.json \
  --mount type=bind,source="$(pwd)"/config.json,target=/usr/src/app/config.json \
  axie-ronin-bot \
  python setup.py
