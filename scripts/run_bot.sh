#!/bin/sh

#docker container rm --force axie-ronin-bot-container > /dev/null 2>&1
docker build -t axie-ronin-bot . && \
docker run \
  -d \
  --name axie-ronin-bot-container \
  --mount type=bind,source="$(pwd)"/credentials.json,target=/usr/src/app/credentials.json,readonly \
  --mount type=bind,source="$(pwd)"/config.json,target=/usr/src/app/config.json \
  --restart on-failure:5 \
  axie-ronin-bot && \
echo 'Axie Ronin bot started and running in background now'