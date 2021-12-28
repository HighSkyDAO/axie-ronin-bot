# Axie Ronin Bot

Telegram bot that allows you to grant access to Axie Infinity account without disclosing Ronin seed.

### Core features
- Adding different user roles and permissions
- Sale, purchase, gift Axies and tokens
- SLP actions: claim and gather

Please note that you are installing the bot yourself on your own server. Only you are responsible for the security of your data. 
**Do not grant access to your server to unauthorized persons.**

## Preparation

First of all, you need a server on which you will run the bot. 
You can register VPS with any convenient cloud provider.
For example, you can use the services of [linode.com](https://www.linode.com/) or [vultr.com](https://www.vultr.com/products/cloud-compute/).
Please note that access to the Axie Infinity website API is blocked for subnets of some providers (For example DigitalOcean). 
You may need to use a proxy to run the bot.

The bot will most likely work on any Linux distribution, 
but this instruction implies that you are using a Debian compatible system, for example, Ubuntu.

As soon as you get root access to your server, you will need to register a Telegram bot.
Use [@BotFather](https://t.me/BotFather) `/newbot` command and get bot username and token. 

![register-bot](https://user-images.githubusercontent.com/454185/145290478-488dce81-f6c2-4a2e-92f6-3c20c0504689.png)

You should also get your internal Telegram id using [https://t.me/my_id_bot](https://t.me/my_id_bot).

To use the bot, you also need an [axieinfinity.com](https://marketplace.axieinfinity.com) account with a verified email, 
and a Seed Recovery Phrase from your [Ronin Wallet](https://wallet.roninchain.com/).


## Installation

Connect to your VPS over [SSH](https://www.linode.com/docs/guides/networking/ssh/).

Download the latest [release](https://github.com/psih31337/AxieRoninBot/tarball/main) and unpack archive.
```shell
mkdir AxieRoninBot && cd AxieRoninBot
curl -fsSL https://github.com/psih31337/AxieRoninBot/tarball/main | tar -xz --strip-components=1
```

### Running in Docker container

If you don't have docker installed on your VPS, do it with the command:
```shell
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && rm get-docker.sh
```

Then you can start the bot installation:
```shell
sudo sh scripts/run_setup.sh
```
To start bot itself run:

```shell
sudo sh scripts/run_bot.sh
```

To see bot logs run:

```shell
sudo sh scripts/show_bot_logs.sh
```

To restart bot:

```shell
sudo sh scripts/restart_bot.sh
```

To remove bot completely, while in the bot folder:

```shell
sudo sh scripts/remove_bot.sh
cd ..
rm -r AxieRoninBot
```


### Manual

You can run this bot without Docker and install the required dependencies manually:

```
sudo apt install -y python3-pip
sudo pip3 install pyTelegramBotAPI web3 ecdsa requests[socks]
python3 setup.py
python3 bot2.py
```

### Using proxy

If you see errors about denying access to the server in the logs after starting the bot, you can use a proxy.
This bot supports http and socks5 proxy types. 
 - `socks5://user:password@192.168.0.1:1080` for socks5
 - `http://user:password@192.168.0.1:1080` for http

To add proxy run the script:
```shell
sudo sh scripts/add_proxy.sh
```

You can also update the file `credentials.json` manually using this format:
```json
    {
        "owner_id": 50123456,
        "seed": "12 seed phrase words",
        "telegram_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "proxy": "socks5://user:password@192.168.0.1:1080"
    }
```

Then you should restart bot using the command:
```shell
sudo sh scripts/restart_bot.sh
```

## How it works

First, you must **Select account** that you will manage. It can be changed in the future.

Then you should be able to do the following **Account** actions:
 - Check your balance
 - Send your tokens (ETH, SLP, AXS)
 - Change your account password
 - Manage your Axies (same as in web interface)

Game **SLP Actions** are also available to you:
 - Gather to one
 - Claim all

Use the **Permissions** button to manage users, who can interact with your account.

To **Add user**, this user **should write any message** to your Telegram bot from his own account first.
Then this user can provide you the Telegram ID, which you can register in the bot. 

Once you have added a new user, you can change user roles and permissions.
Please note that if you want to allow sending tokens or Axie to another account, you must add the required ronin wallets to the whitelist.
