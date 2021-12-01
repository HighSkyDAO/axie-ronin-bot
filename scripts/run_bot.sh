#!/bin/sh

docker build -t axie-ronin-bot . && \
docker run \
  -d \
  --name axie-ronin-bot-container \
  --mount type=bind,source="$(pwd)"/credentials.json,target=/usr/src/app/credentials.json,readonly \
  --mount type=bind,source="$(pwd)"/config.json,target=/usr/src/app/config.json \
  --restart unless-stopped \
  axie-ronin-bot