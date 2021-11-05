import json
import sys 

assert sys.version_info >= (3, 5)
tid = int(input("Enter Your Telegram ID: "))
token = input("Enter Your Telegram Token: ")
seed = input("Enter Your Seed from ronin: ")
accs = int(input("How many accounts to load?\n(-1 mean until mail not assigned on market)\n> "))

open('credentials.json', 'wb').write(json.dumps({
    "owner_id": tid,
    "telegram_token": token,
    "seed": seed,
    "fixed_accounts": accs
}, indent=4).encode('utf-8'))