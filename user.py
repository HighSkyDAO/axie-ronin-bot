import ronin
import threading
import json
import traceback
from ronin import BotError
from seed import mnemonic_to_private_key, ETH_DERIVATION_PATH

wrt = threading.Lock()
levels_to_name = {2: "manager", 8: "admin", 9: "owner"}
name_to_levels = {}
for k in levels_to_name:
    name_to_levels[levels_to_name[k]] = k
        
class User():
    def __init__(self, uid, new=False):
        self.uid = uid
        self.wallet_addr = ""
        self.permission_level = 0
        self.permissions = {"claim": False, "send": False, "buy_axie": False, "sell_axie": False, "breed_and_morph": False, "gift_axie": False}
        
        self.command = "/start"
        self.page = []
        self.username = ""
        self.args = []
        
        self.page_btns = 0
        self.btns = {}
        if new:
            CONFIG.save_config()
    
    def set_perm_all(self, val):
        for k in self.permissions:
            self.permissions[k] = val
            
    def get_readable_name(self):
        return f"{self.uid} {self.username}"
    
    def select_command(self, cmd):
        self.command = cmd
        self.args = []
        
    def set_perm_level(self, level):
        self.permission_level = level
        if self.permission_level >= name_to_levels['admin']:
            self.set_perm_all(True)
            
        CONFIG.save_config()
        
    def use_wallet(self, wallet_addr):
        if not wallet_addr.isalnum():
            raise BotError("Bad wallet_addr")
                        
        if wallet_addr not in CONFIG.wallets:
            raise BotError("Account doesnt exist")
        
        if self.uid not in CONFIG.allowed_users and self.permission_level < name_to_levels["admin"]:
            raise BotError("You dont have permission")
        
        self.wallet_addr = wallet_addr
        CONFIG.save_config()
        return self.get_wallet()
        
    def get_wallet(self):            
        if self.wallet_addr not in CONFIG.wallets:
            raise BotError("Select account")
            
        return CONFIG.wallets[self.wallet_addr]

class CONFIG(object):
    owner_id = 0
    seed = ""
    telegram_token = ""
    
    send_limit = {"ETH": 0, "SLP": 0, "AXS": 0}
    axie_buy_max = 0
    axie_sell_min = 0
    axie_sell_max = 0
    
    whitelist = {}
    allowed_users = set()
    wallets = {}
    users = {}
    
    def get_readable_name(addr):
        if addr in CONFIG.wallets:
            return CONFIG.wallets[addr].get_readable_name()
        elif addr in CONFIG.whitelist:
            return f"'{CONFIG.whitelist[addr]['name']}' '{addr[2:6]}...{addr[-4:]}'"
        return addr.replace("ronin:", "0x")
                
    def load_users():
        if CONFIG.owner_id not in CONFIG.users:
            CONFIG.users[CONFIG.owner_id] = User(CONFIG.owner_id)
        
        CONFIG.allowed_users.add(CONFIG.owner_id)
        CONFIG.users[CONFIG.owner_id].set_perm_level(name_to_levels["owner"])
        
    def add_allowed(user_id):
        CONFIG.allowed_users.add(user_id)
        CONFIG.save_config()
        
    def set_max_send(val):
        CONFIG.save_config()
        
    def add_whitelist(addr, name):
        CONFIG.whitelist[addr] = {"name": name}
        CONFIG.save_config()
    
    def del_whitelist(addr):
        del CONFIG.whitelist[addr]
        CONFIG.save_config()
        
    def save_config():
        jOut = {
            "send_limit": CONFIG.send_limit,
            "axie_buy_max": CONFIG.axie_buy_max,
            "axie_sell_max": CONFIG.axie_sell_max,
            "axie_sell_min": CONFIG.axie_sell_min,
            "whitelist": CONFIG.whitelist,
            "allowed_users": list(CONFIG.allowed_users),
            "users": {},
            "wallets": {}
        }
        
        for uid in CONFIG.users:
            user = CONFIG.users[uid]
            jOut['users'][uid] = {'wallet_addr': user.wallet_addr, 'permission_level': user.permission_level, 'permissions': user.permissions}
            
        for wal in CONFIG.wallets:
            if CONFIG.wallets[wal].market_pass != "-":
                jOut['wallets'][wal] = {'password': CONFIG.wallets[wal].market_pass}
            
        with wrt:
            out = json.dumps(jOut, indent=4).encode('raw_unicode_escape')
            f = open("config.json", 'wb')
            f.write(out)
            f.close()
    
    def fill_wallets():
        i = 0
        while True:
            private_key = mnemonic_to_private_key(CONFIG.seed, str_derivation_path=f'{ETH_DERIVATION_PATH}/{i}')
            acc = ronin.Account(private_key, True)
            if acc.market_mail == "-":
                break
                
            print("Imported: %s"%acc.addr)
            CONFIG.wallets[acc.addr] = acc
            CONFIG.whitelist[acc.addr] = {"name": acc.get_readable_name()}
            i += 1
        CONFIG.seed = ""
        
            
    def load_config():
        jIn = json.loads(open("config.json", 'rb').read())
        CONFIG.send_limit = jIn['send_limit']
        CONFIG.axie_buy_max = jIn['axie_buy_max']
        CONFIG.axie_sell_max = jIn['axie_sell_max']
        CONFIG.axie_sell_min = jIn['axie_sell_min']
        CONFIG.whitelist = jIn['whitelist']
        CONFIG.allowed_users = set(jIn['allowed_users'])
        
        creds = json.loads(open("credentials.json", 'rb').read())
        CONFIG.owner_id = creds['owner_id']
        CONFIG.seed = creds['seed']
        CONFIG.telegram_token = creds['telegram_token']
        CONFIG.fill_wallets()
        
        for wal in jIn['wallets']:
            if wal in CONFIG.wallets:
                CONFIG.wallets[wal].market_pass = jIn['wallets'][wal]['password']
        
        for uid in jIn['users']:
            uid_ = int(uid)
            u = User(uid_)
            u.wallet_addr = jIn['users'][uid]['wallet_addr']
            u.permission_level = jIn['users'][uid]['permission_level']
            if 'permission' in jIn['users'][uid]:
                u.permissions = jIn['users'][uid]['permissions']
                
            CONFIG.users[uid_] = u
            
        for uid in CONFIG.allowed_users:
            if uid not in CONFIG.users:
                CONFIG.users[uid] = User(uid)