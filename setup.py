import json
import sys 

assert sys.version_info >= (3, 5)
tid = int(input("Enter your Telegram ID, you can get it from https://t.me/my_id_bot (Example: 54123456): "))
token = input("Enter your Telegram Token, you can get it from BotFather https://t.me/BotFather (Example: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11): ")
seed = input("Enter your seed from Ronin, 12 words: ")
proxy = input('Enter your proxy in a format or press Enter to skip (Example: socks5://user:password@example.com:1080): ')

credentials = {
    "owner_id": tid,
    "telegram_token": token,
    "seed": seed,
}
if proxy.strip():
    credentials["proxy"] = proxy

credentials_dump = json.dumps(credentials, indent=4).encode('utf-8')
open('credentials.json', 'wb').write(credentials_dump)
