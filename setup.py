import json
import sys 

assert sys.version_info >= (3, 5)
tid = int(input("Enter Your Telegram ID (you can get it from https://t.me/my_id_bot): "))
token = input("Enter Your Telegram Token (from BotFather https://t.me/BotFather): ")
seed = input("Enter Your Seed from Ronin (12 words): ")
accs = int(input("How many Ronin accounts to load?\n(-1 mean until mail not assigned on market)\n> "))

open('credentials.json', 'wb').write(json.dumps({
    "owner_id": tid,
    "telegram_token": token,
    "seed": seed,
    "fixed_accounts": accs
}, indent=4).encode('utf-8'))
