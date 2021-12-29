#!/bin/sh

CREDENTIALS_FILE=credentials.json
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "credentials.json file doesn't exist, just run a normal setup: sudo sh scripts/run_setup.sh"
    exit 1
fi


docker build -t axie-ronin-bot . && \
docker run \
  -it \
  --rm \
  --name axie-ronin-bot-set-proxy \
  --mount type=bind,source="$(pwd)"/credentials.json,target=/usr/src/app/credentials.json \
  --mount type=bind,source="$(pwd)"/config.json,target=/usr/src/app/config.json \
  axie-ronin-bot \
  python set_proxy.py
