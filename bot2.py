import telebot
import binascii
import traceback
import ronin
import random
import time
from user import User, CONFIG, name_to_levels
from web3 import Web3
from ronin import BotError
from hexbytes import HexBytes
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

CONFIG.load_config()
CONFIG.load_users()
users = CONFIG.users
bot = telebot.TeleBot(CONFIG.telegram_token)
BUTTON_BACK_CANCEL = "Cancel/Back"
select_next_action = "Please select your next action"

def wallet_balance(wal, isAdmin=False):
    eth_bal = wal.balance()
    slp_bal = wal.slp_balance()
    axs_bal = wal.axs_balance()
    
    unc = "%d"%slp_bal['claimable']
    if slp_bal['allow']:
        unc += " \u2705"
    else:
        unc += " \u274c"
    
    resp =  "`%d. %s`\n"%(wal.id, wal.market_name)
    resp += "Email: `%s`\n"%(wal.market_mail)
    if isAdmin:
        resp += "Password: `%s`\n"%(wal.market_pass)
    
    resp += "Address: `%s`\n"%wal.addr
    resp += "Balance:\n    ETH `%.8f`\n    SLP `%d, %s`\n    AXS `%d`\n"%(eth_bal, slp_bal['value'], unc, axs_bal)
    resp += "Axie list: "
    
    for axie in wal.get_axies():
        resp += "\n    %s"%(axie['id'])
        if(axie['stage'] <= 2):
            info = wal.get_axie_info(int(axie['id']))
            resp += " \U0001f95a"
            if time.time() - info['birthDate'] < 5*24*60*60:
                resp += " \u274c"
            else:
                resp += " \u2705"
    return (resp, eth_bal, slp_bal, axs_bal)
    
def cmd_balance(user, message):
    wal = user.get_wallet() 
    resp = wallet_balance(wal, user.permission_level >= name_to_levels['admin'])[0]
    move_back(user, resp)
    
def cmd_allow(user, message):
    if user.permission_level < name_to_levels["admin"]:
        raise BotError("You dont have permission")
        
    if len(user.args) == 0:
        return "Enter account id", []
        
    tuid = int(user.args[0])
    if tuid not in users:
        raise BotError("User doesnt exist")
        
    CONFIG.add_allowed(tuid)
    move_back(user, "Done")
    
def cmd_use(user, message):
    if len(user.args) == 0:
        return "Select Account", {"text": [CONFIG.wallets[x].get_readable_name() for x in CONFIG.wallets], "callback_data": [wal for wal in CONFIG.wallets]}
    
    wal = CONFIG.wallets[user.args[0]]
    
    user.use_wallet(wal.addr)
    
    resp = "Selected:\n%s"%(wallet_balance(wal, user.permission_level >= name_to_levels['admin'])[0])
    move_back(user, resp)

def cmd_new_pass(user, message):
    if len(user.args) == 0:
        return "Enter old password", []
    
    old_pass = user.args[0]
    wal = user.get_wallet() 
    new_pass = wal.change_pass(old_pass)
    CONFIG.save_config()
    
    move_back(user, "Success, new password: %s"%new_pass)  

def cmd_info_all(user, message):
    max_in_line = 0
    wdict = CONFIG.wallets
    uid = user.uid
    
    total_eth = 0
    total_slp = 0
    total_axs = 0
    
    eth_resp = ""
    axs_resp = ""
    
    slp_total = 0
    slp_can_claim = 0
    slp_no_claim = 0
    
    slp_total_resp = ""
    slp_can_claim_resp = ""
    slp_no_claim_resp = ""
    
    for addr in wdict:
        wal = wdict[addr]
            
        resp, eth_bal, slp_bal, axs_bal = wallet_balance(wal)
        total_eth += eth_bal
        if eth_bal > 0:
            eth_resp += "    - %s: %f\n"%(wal.get_readable_name(), eth_bal)
            
        total_axs += axs_bal
        if axs_bal > 0:
            axs_resp += "    - %s: %f\n"%(wal.get_readable_name(), axs_bal)
        
        slp_total += slp_bal['value']
        if slp_bal['value'] > 0:
            slp_total_resp += "    - %s: %f\n"%(wal.get_readable_name(), slp_bal['value'])
            
        if slp_bal['allow']:
            slp_can_claim += slp_bal['claimable']
            
            if slp_bal['claimable'] > 0:
                slp_can_claim_resp += "    - %s: %f\n"%(wal.get_readable_name(), slp_bal['claimable'])
        else:
            slp_no_claim += slp_bal['claimable']
            
            if slp_bal['claimable'] > 0:
                slp_no_claim_resp += "    - %s: %f\n"%(wal.get_readable_name(), slp_bal['claimable'])
        bot.send_message(uid, resp.replace(".", "\\.").replace("-", "\\-"), parse_mode="MarkdownV2")
    
    bot.send_message(uid, f"TOTAL ETH: {total_eth:.8f}\n{eth_resp}\nTOTAL AXS: {total_axs}\n{axs_resp}\nTOTAL SLP: {slp_total}\n{slp_total_resp}\nTOTAL CLAIMABLE SLP: {slp_can_claim}\n{slp_can_claim_resp}\nTOTAL LOCKED SLP: {slp_no_claim}\n{slp_no_claim_resp}")
   
    
def cmd_send(user, message):
    if not user.permissions['send']:
        raise BotError("You dont have permission")
        
    if len(user.args) == 0:
        return "What send?", list(CONFIG.send_limit.keys())
          
    type = user.args[0]
    if type not in CONFIG.send_limit:
        raise BotError("Wrong type! Available: %s"%(', '.join(CONFIG.send_limit.keys()))) 
        
    if len(user.args) == 1:
        return "Enter ronin address", {"text": [CONFIG.get_readable_name(wal) for wal in CONFIG.whitelist], "callback_data": [wal for wal in CONFIG.whitelist]}
        
    to_addr = user.args[1]
    
    if len(user.args) == 2:
        max_val = CONFIG.send_limit[type]
        if to_addr in CONFIG.wallets:
            max_val = "unlimited"
            
        return f"Enter value, max {max_val}", []
        
    value = user.args[2]    
    wal = user.get_wallet() 
    
    if to_addr not in CONFIG.whitelist and user.permission_level < name_to_levels["admin"]:
        raise BotError("Destination address not in whitelist")
        
    if float(value) > CONFIG.send_limit[type] and user.permission_level < name_to_levels["admin"] and to_addr not in CONFIG.wallets:
        raise BotError('Max transaction limit %f'%CONFIG.send_limit[type])
        
    try:
        bot.send_message(user.uid, "Handle you request...")
        txID = wal.send(to_addr, value, type)
    except binascii.Error:
        raise BotError('Bad address or value format')
    
    move_back(user, "Success\ntxID: `%s`"%txID)  

def cmd_whitelist(user, message):
    if user.permission_level < name_to_levels["admin"]:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Enter ronin address", []
        
    if len(args) == 1:
        return "Enter name", []
        
    address = args[0].replace("ronin:", "0x")
    name = args[1].replace("'", "")
    if not Web3.isAddress(address):
        raise BotError("Bad address")
        
    if len(address) != 42 or not address.startswith("0x"):
        raise BotError("Bad addr")
    
    CONFIG.add_whitelist(address, name)
    move_back(user, "Success")

def cmd_whitelist_del(user, message):
    if user.permission_level < name_to_levels["admin"]:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Enter name", {"text": [CONFIG.get_readable_name(wal) for wal in CONFIG.whitelist], "callback_data": [wal for wal in CONFIG.whitelist]}
        
    address = args[0]
    CONFIG.del_whitelist(address)
    move_back(user, "Success")
    
def cmd_set_level(user, message):
    if user.permission_level < name_to_levels["admin"]:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Select or enter user", [str(id) for id in CONFIG.allowed_users]
        
    if len(args) == 1:
        return "Select status?", list(name_to_levels.keys())
        
    tuid = int(args[0])
    level = name_to_levels[args[1]]
    if user.permission_level < level:
        raise BotError("Cant set level of target user more than you have")
        
    if tuid not in users:
        raise BotError("User %d doesn't exist"%tuid)
    
    users[tuid].set_perm_level(level)
    move_back(user, "Success")

def cmd_gift(user, message):
    if not user.permissions['gift_axie']:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Select axie", [ax['id'] for ax in user.get_wallet().get_axies()]
        
    if len(args) == 1:
        return "Enter ronin address", {"text": [CONFIG.get_readable_name(wal) for wal in CONFIG.whitelist], "callback_data": [wal for wal in CONFIG.whitelist]}
    
    to_addr = user.args[1]
    
    if to_addr not in CONFIG.whitelist and user.permission_level < name_to_levels["admin"]:
        raise BotError("Destination address not in whitelist")
            
    wal = user.get_wallet()   
    tx = wal.gift_axie(int(args[0]), to_addr)
    move_back(user, "Success\ntxID: `%s`"%tx)  
    
def cmd_sell_auc(user, message):
    if not user.permissions['sell_axie']:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Select axie", [ax['id'] for ax in user.get_wallet().get_axies()]
    aid = int(args[0])
    
    if len(args) == 1:
        return "Enter start price", []
        
    price1 = float(args[1])
    if price1 > CONFIG.axie_sell_max or price1 < CONFIG.axie_sell_min:
        raise BotError(f"Sell limit {CONFIG.axie_sell_max} > start price > {CONFIG.axie_sell_min}")
        
    if len(args) == 2:
        return "Enter end price", []
        
    price2 = float(args[2])
    if price2 > CONFIG.axie_sell_max or price2 < CONFIG.axie_sell_min:
        raise BotError("Sell limit")
    
    if len(args) == 3:
        return "Enter max days", ["1", "2", "3"]
        
    days = int(args[3])
    wal = user.get_wallet() 
    tx = wal.sell_axie(aid, price1, price2, days)  
    move_back(user, "Success\ntxID: `%s`"%tx)  
    
def cmd_sell_fix(user, message):
    if not user.permissions['sell_axie']:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Select axie", [ax['id'] for ax in user.get_wallet().get_axies()]
        
    if len(args) == 1:
        return "Enter price", []
            
    aid = int(args[0])
    price = float(args[1])
    if price > CONFIG.axie_sell_max or price < CONFIG.axie_sell_min:
        raise BotError("Sell limit")
        
    wal = user.get_wallet() 
    tx = wal.sell_axie(aid, price, price, 1)
    move_back(user, "Success\ntxID: `%s`"%tx)  

def cmd_buy(user, message):
    if not user.permissions['buy_axie']:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Enter axie id from market", []
        
    wal = user.get_wallet()   
    info = wal.get_axie_info(int(args[0]))
    price = int(info['auction']['suggestedPrice'])
    if Web3.fromWei(price, 'ether') > CONFIG.axie_buy_max:
        raise BotError(f"Buy limit {CONFIG.axie_buy_max}")
            
    tx = wal.buy_axie(info)
    move_back(user, "Success\ntxID: `%s`"%tx)  
    
def cmd_morph(user, message):
    if not user.permissions['breed_and_morph']:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:        
        return "Select axie", [ax['id'] for ax in user.get_wallet().get_axies() if ax['stage'] <= 2]
        
    wal = user.get_wallet()
    resp = wal.morph_axie(int(args[0]))
    msg = "Fail"
    if resp:
        msg = "Success"
    
    move_back(user, msg)
        
def cmd_breed(user, message):
    if not user.permissions['breed_and_morph']:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Select axie 1", [ax['id'] for ax in user.get_wallet().get_axies()]
    ax1 = int(args[0])
        
    if len(args) == 1:
        return "Select axie 2", [ax['id'] for ax in user.get_wallet().get_axies() if ax['id'] != ax1]
        
    wal = user.get_wallet() 
    ax2 = int(args[1])
    
    if(ax1 == ax2):
        raise BotError("Cant breed with same id")
        
    ax_list = wal.get_axies()
    ax_ids = [int(x['id']) for x in ax_list]
    
    if ax1 not in ax_ids:
        raise BotError("Axie1 not in your inventory")
        
    if ax2 not in ax_ids:
        raise BotError("Axie2 not in your inventory")
        
    txID = wal.breed(ax1, ax2)
    move_back(user, "Success\ntxID: `%s`"%txID)  

    
def cmd_claim_all(user, message):
    if not user.permissions['claim']:
        raise BotError("You dont have permission")
        
    resp = "Summary:\n"
    for wal_id in CONFIG.wallets:
        wal = CONFIG.wallets[wal_id]
        slp_bal = wal.slp_balance()
        if slp_bal['allow']:
            txID = wal.claim_slp()
            resp += f"Claim {wal.market_name} {txID}\n"
        
    bot.send_message(user.uid, resp)  
        
def cmd_claim_gather(user, message):
    if not user.permissions['claim']:
        raise BotError("You dont have permission")
        
    args = user.args
    if len(args) == 0:
        return "Enter ronin address", {"text": [CONFIG.get_readable_name(wal) for wal in CONFIG.whitelist], "callback_data": [wal for wal in CONFIG.whitelist]}
    
    to_addr = user.args[0]
        
    if to_addr not in CONFIG.whitelist and user.permission_level < name_to_levels["admin"]:
        raise BotError("Destination address not in whitelist")
      
    resp = "Summary:\n"
    for wal_id in CONFIG.wallets:
        if wal_id == to_addr:
            continue
            
        wal = CONFIG.wallets[wal_id]
        slp_bal = wal.slp_balance()
        val = slp_bal['value']
        
        if val > 0:
            txID = wal.send(to_addr, val, "SLP")
            resp += f"Send {val}SLP from {wal.market_name} \ntxID: {txID}\n"
    
    move_back(user, resp)

def cmd_change_perm(user, message):
    if user.permission_level < name_to_levels['admin']:
        raise BotError("You dont have permission")
    
    if len(user.args) == 0:
        return "Select User", [str(x) for x in users]
    tuser = users[int(user.args[0])]
    
    if len(user.args) == 1:
        rdbl_perm = f"User {user.args[0]} permissions:\n"
        for perm in tuser.permissions:
            rdbl_perm += f"Can user {perm.replace('_', ' ')}: {tuser.permissions[perm]}\n"
        bot.send_message(user.uid, rdbl_perm)
        
        return "Can user claim?", ["Yes", "No"]
    tuser.permissions['claim'] = user.args[1] == "Yes"
    
    if len(user.args) == 2:
        return "Can user send?", ["Yes", "No"]
    tuser.permissions['send'] = user.args[2] == "Yes"
    
    if len(user.args) == 3:
        return "Can user buy axie?", ["Yes", "No"]
    tuser.permissions['buy_axie'] = user.args[3] == "Yes"
    
    if len(user.args) == 4:
        return "Can user sell axie?", ["Yes", "No"]
    tuser.permissions['sell_axie'] = user.args[4] == "Yes"
    
    if len(user.args) == 5:
        return "Can user gift axie?", ["Yes", "No"]
    tuser.permissions['gift_axie'] = user.args[5] == "Yes"
    
    if len(user.args) == 6:
        return "Can user breed and morph?", ["Yes", "No"]
    tuser.permissions['breed_and_morph'] = user.args[6] == "Yes"
    
    CONFIG.save_config()
    move_back(user, "Done")
    
def move_back(user, text):
    if len(user.page) > 0:
        if user.page[-1] != user.command:
            command = user.page.pop()
        else:
            if len(user.page) > 1:
                user.page.pop()
                command = user.page.pop()
            else:
                command = "/start"
    else:
        command = "/start"
            
    bot.send_message(user.uid, text.replace(".", "\\.").replace("-", "\\-"), parse_mode="MarkdownV2")  
    if "page_" in command_list[command].__name__ or command == "/start":
        command_list[command](user, None)
    
def gen_markup(listb, width=2, exclude_back=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row_width = width
    if(not exclude_back):
        markup.add(BUTTON_BACK_CANCEL)
    markup.add(*listb)
    return markup
    
def cmd_start(user, message):   
    user.page = []
    buttons = []
    if user.wallet_addr == "":
        buttons.append("Select Account")
    else:
        buttons.append("Account")
        
    if user.permission_level >= name_to_levels['admin']:
        buttons.append("Permissions")
    
    buttons += ["Check all balance", "SLP Actions"]
    bot.send_message(user.uid, f"Hi, your id: {user.uid}", reply_markup=gen_markup(buttons, exclude_back=True))
    
def page_axies(user, message):
    if message:
        user.page.append("Axies")
        
    buttons = ["Buy", "Sell auction", "Sell fixed", "Gift", "Breed", "Morph"]
    bot.send_message(user.uid, select_next_action, reply_markup=gen_markup(buttons), parse_mode="MarkdownV2")

def page_account(user, message):
    if message:
        user.page.append("Account")
        wal = user.get_wallet()
        resp =  "Current Account:\n%d. `%s`\n"%(wal.id, wal.market_name)
        resp += "Email: `%s`\n"%(wal.market_mail)
        resp += "Address: `%s`\n"%wal.addr
    else:
        resp = select_next_action
        
    msg = resp.replace(".", "\\.").replace("-", "\\-")
    
    buttons = ["Balance", "Send crypto", "Change password", "Change Account", "Axies"]
    bot.send_message(user.uid, msg, reply_markup=gen_markup(buttons), parse_mode="MarkdownV2")

def page_permisson(user, message):
    if message:
        user.page.append("Permissions")
        
    buttons = ["Add user", "Change status", "Add whitelist", "Delete whitelist", "Change user permission"]
    bot.send_message(user.uid, select_next_action, reply_markup=gen_markup(buttons), parse_mode="MarkdownV2")

def page_slps(user, message):
    if message:
        user.page.append("SLP Actions")
        
    buttons = ["Gather to one", "Claim All"]
    bot.send_message(user.uid, select_next_action, reply_markup=gen_markup(buttons), parse_mode="MarkdownV2")
    
command_list = {
    "Account": page_account,
    "Axies": page_axies,
    "/start": cmd_start,
    "Permissions": page_permisson,
    "SLP Actions": page_slps,
    
    "Select Account": cmd_use,
     
    "Balance": cmd_balance,
    "Send crypto": cmd_send,
    "Change password": cmd_new_pass,
    "Change Account": cmd_use,
    
    "Check all balance": cmd_info_all,
   
    "Add user": cmd_allow,
    "Add whitelist": cmd_whitelist,
    "Delete whitelist": cmd_whitelist_del,
    "Change status": cmd_set_level,
    "Change user permission": cmd_change_perm,
    
    
    "Buy": cmd_buy,
    "Gift": cmd_gift,
    "Sell auction": cmd_sell_auc,
    "Sell fixed": cmd_sell_fix,
    "Breed": cmd_breed,
    "Morph": cmd_morph,
    
    "Gather to one": cmd_claim_gather,
    "Claim All": cmd_claim_all
}

def gen_inline_markup(datas, size):
    if len(datas['text']) != len(datas['callback_data']):
        raise BotError("Missmatch len gen_inline_markup")
        
    markup = InlineKeyboardMarkup()
    markup.row_width = size
    
    for i in range(len(datas['text'])):
        print(datas['text'][i])
        print(datas['callback_data'][i])
        markup.add(InlineKeyboardButton(datas['text'][i], callback_data=datas['callback_data'][i]))
    return markup
    
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(call.data)
    try:
        uid = call.from_user.id
        cid = call.message.chat.id
        mid = call.message.message_id
        
        user = users[uid]
        user.args.append(call.data)
        
        res = command_list[user.command](user, call.message)
        if res:
            msg = res[0]
            btns = res[1]
            if not isinstance(res[1], dict):
                btns = {"text": res[1], "callback_data": res[1]}
            bot.edit_message_text(msg, cid, mid, reply_markup=gen_inline_markup(btns, 1))
        else:
            bot.delete_message(cid, mid)
    except BotError as be:
        bot.send_message(uid, 'Error: %s'%be.msg)
        if len(user.args) > 0:
            user.args.pop()
    except:
        bot.send_message(uid, 'Error while handle your request...')
        traceback.print_exc()
        
    bot.answer_callback_query(call.id)
        
@bot.message_handler(content_types=['text'])
def parse_text(message):
    print(HexBytes(message.text.encode('raw_unicode_escape')))    
    
    if message.chat.type != 'private':
        return
    
    command = message.text
    uid = message.from_user.id
    if uid not in users:
        users[uid] = User(uid, True)
    #users[uid].username = message.from_user.username
    
    user = users[uid]
    
    if uid not in CONFIG.allowed_users:
        bot.send_message(uid, 'Not Authorized. UID: %d\nOnly admin can grant access to this bot'%uid)
        return    
    
    if command == BUTTON_BACK_CANCEL:
        if len(user.page) > 0:
            if user.page[-1] != user.command:
                command = user.page.pop()
            else:
                if len(user.page) > 1:
                    user.page.pop()
                    command = user.page.pop()
                else:
                    command = "/start"
        else:
            command = "/start"
    try:       
        if command not in command_list:
            user.args.append(command)
            command = user.command
        else:
            user.select_command(command)     
        
        res = command_list[command](user, message)
        if res:
            msg = res[0]
            btns = res[1]
            if not isinstance(res[1], dict):
                btns = {"text": res[1], "callback_data": res[1]}
            bot.send_message(user.uid, msg, reply_markup=gen_inline_markup(btns, 1))
    except BotError as be:
        bot.send_message(uid, 'Error: %s'%be.msg)
        if len(user.args) > 0:
            user.args.pop()
    except:
        bot.send_message(uid, 'Error while handle your request...')
        traceback.print_exc()

    print(user.page)    
print("Started")     
bot.polling(none_stop=True)