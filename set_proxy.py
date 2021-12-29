import os.path
import json

credentials_filename = 'credentials.json'
if not os.path.isfile(credentials_filename):
    print("credentials.json file doesn't exist, just run a normal setup: sudo sh scripts/run_setup.sh")
    exit(1)

with open(credentials_filename) as json_file:
    credentials = json.load(json_file)

proxy = input('Enter your proxy (Example: socks5://user:password@example.com:1080): ')
if not proxy.strip():
    print('Proxy was empty, exiting')
    exit(2)

credentials["proxy"] = proxy
print('Proxy set successfully')
credentials_dump = json.dumps(credentials, indent=4).encode('utf-8')
open('credentials.json', 'wb').write(credentials_dump)
