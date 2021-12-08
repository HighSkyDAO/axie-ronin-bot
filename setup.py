import json
import sys 

assert sys.version_info >= (3, 5)
tid = int(input("Enter your Telegram ID (you can get it from https://t.me/my_id_bot): "))
token = input("Enter your Telegram Token (from BotFather https://t.me/BotFather): ")
seed = input("Enter your seed from Ronin (12 words): ")
proxy = input("Enter your socks5 proxy in a format or press Enter to skip (example: user:password@example.com:1080): ")

credentials = {
    "owner_id": tid,
    "telegram_token": token,
    "seed": seed,
}
if not proxy.strip():
    credentials["proxy"] = f"socks5://{proxy}"

credentials_dump = json.dumps(credentials, indent=4).encode('utf-8')
open('credentials.json', 'wb').write(credentials_dump)
