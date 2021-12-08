import json
import sys 

assert sys.version_info >= (3, 5)
tid = int(input("Enter Your Telegram ID: "))
token = input("Enter Your Telegram Token: ")
seed = input("Enter Your Seed from ronin: ")

open('credentials.json', 'wb').write(json.dumps({
    "owner_id": tid,
    "telegram_token": token,
    "seed": seed,
}, indent=4).encode('utf-8'))
