# Installation
Pure debian 11 (amd64)
```
apt install -y git python3-pip
pip3 install pyTelegramBotAPI web3 ecdsa

git clone https://github.com/psih31337/AxieRoninBot
cd AxieRoninBot
python3 setup.py
python3 bot2.py
```

### Running in Docker container

This section assumes you've already downloaded project's source code with git.
To install Docker run this or follow instructions from [official guide](https://docs.docker.com/engine/install/):
```shell
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
```

You will first need to set up your accounts.
Create a new bot in a Telegram [BotFather](https://t.me/BotFather).
Then add info about your Telegram bot and Ronin by running the following script:
```shell
sudo sh scripts/run_setup.sh
```

To start bot itself run:
```shell
sudo sh scripts/run_bot.sh
```

To see bot logs run:
```shell
sudo sh show_bot_logs.sh
```