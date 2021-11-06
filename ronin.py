import requests, json
import hashlib
import string
import random
import time
from typing import NamedTuple
from eth_utils.curried import to_bytes
from eth_keys import keys
from web3 import Web3, HTTPProvider
from hexbytes import HexBytes

class BotError(BaseException):
    def __init__(self, errmsg):
        self.msg = errmsg

class SignableMessage(NamedTuple):
    version: bytes  # must be length 1
    header: bytes  # aka "version specific data"
    body: bytes  # aka "data to sign"
    
def encode_defunct(
        primitive: bytes = None,
        *,
        hexstr: str = None,
        text: str = None) -> SignableMessage:
        
    message_bytes = to_bytes(primitive, hexstr=hexstr, text=text)
    msg_length = str(len(message_bytes)).encode('utf-8')

    return SignableMessage(
        b'E',
        b'thereum Signed Message:\n' + msg_length,
        message_bytes,
    )
    
class Account():
    def __init__(self, private_key, login=False):
        self.private_key = keys.PrivateKey(HexBytes(private_key))
        self.public_key = self.private_key.public_key        
        self.addr = "0x%s"%Web3.keccak(self.public_key.to_bytes()).hex()[-40:]
        
        self.market_name = "-"
        self.market_mail = "-"
        self.market_pass = "-"
        self.id = CONFIG.acc_id
        CONFIG.acc_id += 1
        self.r = requests.Session() 
        self.auth = False
            
        if login:
            self.login_market()
        
    def create():
        return Account()
    
    def send_req(self, url, reqData):
        
        error = ""
        for i in range(5):
            resp = self.r.post(url, json=reqData)
            jData = json.loads(resp.text)
            if "errors" in jData:
                error = ''.join("%s\n"%x['message'] for x in jData["errors"])
                print(error)
            else:
                return jData
            
        raise BotError("Market request error "+error)
        
    def balance(self):
        if not self.auth:
            self.login_market()
            
        data = ronin_contract.functions.balanceOf(Web3.toChecksumAddress(self.addr)).buildTransaction({'gas': 1000000, 'gasPrice': 0})
        resp = common_eth.call(data)
        return Web3.fromWei(int(HexBytes(resp).hex(), 16), 'ether')
        
    def get_readable_name(self):
        return f"{self.id}. '{self.market_name}' '{self.addr[2:6]}...{self.addr[-4:]}'"
        
    def login_market(self):
        reqData = {"operationName":"CreateRandomMessage","variables":{},"query":"mutation CreateRandomMessage {\n  createRandomMessage\n}\n"}
        jData = self.send_req(CONFIG.marketql, reqData)
        
        msg = jData["data"]["createRandomMessage"]
        sgndMsg = self.sign(msg)
        reqData = {"operationName":"CreateAccessTokenWithSignature","variables":{"input":{"mainnet":"ronin","owner":self.addr,"message":msg,"signature":sgndMsg.signature.hex()}},
            "query":"mutation CreateAccessTokenWithSignature($input: SignatureInput!) {\n  createAccessTokenWithSignature(input: $input) {\n    newAccount\n    result\n    accessToken\n    __typename\n  }\n}\n"}
        
        jData = self.send_req(CONFIG.marketql, reqData)
        if jData['data']["createAccessTokenWithSignature"]["result"]:
            self.r.headers['Authorization'] = "Bearer "+jData['data']["createAccessTokenWithSignature"]["accessToken"]
        else:
            print(jData)
        
        reqData = {"operationName":"GetProfileBrief","variables":{},"query":"query GetProfileBrief {\n  profile {\n    ...ProfileBrief\n    __typename\n  }\n}\n\nfragment ProfileBrief on AccountProfile {\n  accountId\n  addresses {\n    ...Addresses\n    __typename\n  }\n  email\n  activated\n  name\n  settings {\n    unsubscribeNotificationEmail\n    __typename\n  }\n  __typename\n}\n\nfragment Addresses on NetAddresses {\n  ethereum\n  tomo\n  loom\n  ronin\n  __typename\n}\n"}
        jData = self.send_req(CONFIG.marketql, reqData)
        if jData['data']['profile']['email']:
            self.market_mail = jData['data']['profile']['email']
        self.market_name = jData['data']['profile']['name']
        self.auth = True
        
    def change_pass(self, old_pass):
        if not self.auth:
            self.login_market()
            
        new_pass = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=16))
        reqData = {"operationName":"UpdatePassword","variables":{"password":new_pass, "oldPassword":hashlib.sha256(old_pass.encode("raw_unicode_escape")).hexdigest()},"query":"mutation UpdatePassword($password: String!, $oldPassword: String!) {\n  updatePassword(newPassword: $password, password: $oldPassword) {\n    result\n    __typename\n  }\n}\n"}
        self.send_req(CONFIG.marketql, reqData)
        
        self.market_pass = new_pass
        return new_pass
    
    def get_slp_info(self):
        if not self.auth:
            self.login_market()
            
        jData = self.send_req(f"https://game-api.skymavis.com/game-api/clients/{self.addr}/items/1/claim", None)
        return jData
    
    def claim_slp(self):
        slp_info = self.get_slp_info()
        from_addr = Web3.toChecksumAddress(self.addr)
        slp_sign = slp_info["blockchain_related"]['signature']
        if not slp_sign or (time.time() - slp_info['last_claimed_item_at'] < 14*24*60*60 and slp_sign['amount'] == slp_info['blockchain_related']['checkpoint']):
            raise BotError("Now you cant claim SLP")
            
        txn = slp_contract.functions.checkpoint(from_addr, slp_sign["amount"], slp_sign["timestamp"], slp_sign['signature'])
        return self.send_raw(txn)
        
    def sign(self, msg):
        message = encode_defunct(text=msg)
        signed_message = free_eth.account.sign_message(message, private_key=self.private_key)
        return signed_message
    
    def get_market_axies(self):
        reqData = {"operationName":"GetAxieBriefList","variables":{"from":0,"size":24,"sort":"PriceAsc","auctionType":"Sale","owner":None,"criteria":{"region":None,"parts":None,"bodyShapes":None,"classes":None,"stages":None,"numMystic":None,"pureness":None,"title":None,"breedable":None,"breedCount":None,"hp":[],"skill":[],"speed":[],"morale":[]}},"query":"query GetAxieBriefList($auctionType: AuctionType, $criteria: AxieSearchCriteria, $from: Int, $sort: SortBy, $size: Int, $owner: String) {\n  axies(auctionType: $auctionType, criteria: $criteria, from: $from, sort: $sort, size: $size, owner: $owner) {\n    total\n    results {\n      ...AxieBrief\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment AxieBrief on Axie {\n  id\n  name\n  stage\n  class\n  breedCount\n  image\n  title\n  battleInfo {\n    banned\n    __typename\n  }\n  auction {\n    currentPrice\n    currentPriceUSD\n    __typename\n  }\n  parts {\n    id\n    name\n    class\n    type\n    specialGenes\n    __typename\n  }\n  __typename\n}\n"}
        resp = self.send_req(CONFIG.marketql, reqData)
        return resp['data']['axies']["results"]
        
    def get_free_send(self):
        data = {"id":CONFIG._id, "jsonrpc":"2.0","params":[self.addr],"method":"eth_getFreeGasRequests"}
        resp = self.send_req(CONFIG.free_rpc, data)
        return resp["result"]
   
    def get_axie_info(self, axie_id):
        data = {"operationName":"GetAxieDetail","variables":{"axieId":"%d"%axie_id},"query":"query GetAxieDetail($axieId: ID!) {\n  axie(axieId: $axieId) {\n    ...AxieDetail\n    __typename\n  }\n}\n\nfragment AxieDetail on Axie {\n  id\n  image\n  class\n  chain\n  name\n  genes\n  owner\n  birthDate\n  bodyShape\n  class\n  sireId\n  sireClass\n  matronId\n  matronClass\n  stage\n  title\n  breedCount\n  level\n  figure {\n    atlas\n    model\n    image\n    __typename\n  }\n  parts {\n    ...AxiePart\n    __typename\n  }\n  stats {\n    ...AxieStats\n    __typename\n  }\n  auction {\n    ...AxieAuction\n    __typename\n  }\n  ownerProfile {\n    name\n    __typename\n  }\n  battleInfo {\n    ...AxieBattleInfo\n    __typename\n  }\n  children {\n    id\n    name\n    class\n    image\n    title\n    stage\n    __typename\n  }\n  __typename\n}\n\nfragment AxieBattleInfo on AxieBattleInfo {\n  banned\n  banUntil\n  level\n  __typename\n}\n\nfragment AxiePart on AxiePart {\n  id\n  name\n  class\n  type\n  specialGenes\n  stage\n  abilities {\n    ...AxieCardAbility\n    __typename\n  }\n  __typename\n}\n\nfragment AxieCardAbility on AxieCardAbility {\n  id\n  name\n  attack\n  defense\n  energy\n  description\n  backgroundUrl\n  effectIconUrl\n  __typename\n}\n\nfragment AxieStats on AxieStats {\n  hp\n  speed\n  skill\n  morale\n  __typename\n}\n\nfragment AxieAuction on Auction {\n  startingPrice\n  endingPrice\n  startingTimestamp\n  endingTimestamp\n  duration\n  timeLeft\n  currentPrice\n  currentPriceUSD\n  suggestedPrice\n  seller\n  listingIndex\n  state\n  __typename\n}\n"}
        resp = self.send_req(CONFIG.marketql, data)
        return resp['data']['axie']
    
    def send_raw(self, txn):
        if self.get_free_send() <= 10:
            raise BotError("Not enough free send count")
            
        from_addr = Web3.toChecksumAddress(self.addr)
        nonce = free_eth.get_transaction_count(from_addr)
        
        txn = txn.buildTransaction({'gas': txn.estimateGas(), 'gasPrice': 0, 'nonce': nonce}) 
        signed_txn = free_eth.account.sign_transaction(txn, self.private_key)
        txHash = free_eth.send_raw_transaction(signed_txn.rawTransaction)
        return HexBytes(txHash).hex()
    
    def gift_axie(self, axie_id, to_addr):
        from_addr = Web3.toChecksumAddress(self.addr)
        to_addr = Web3.toChecksumAddress(to_addr)
        if from_addr == to_addr:
            raise BotError("Cant gift yourself")
            
        info = self.get_axie_info(axie_id)
        if info['owner'] != self.addr:
            raise BotError("This is NOT your axie")
            
        txn = axies_contract.functions.safeTransferFrom(from_addr, to_addr, axie_id)
        return self.send_raw(txn)
        
    def buy_axie(self, info):
        seller_addr = Web3.toChecksumAddress(info['owner'])
        price = int(info['auction']['currentPrice'])
        if info['owner'] == self.addr:
            raise BotError("This is your axie")
            
        if Web3.fromWei(price, 'ether') > self.balance():
            raise BotError("Not enough ETH fro buy")
        
        txn = market_contract.functions.settleAuction(seller_addr, CONFIG.contracts[info["chain"]], price, int(info['auction']["listingIndex"]), int(info['auction']['state']))
        return self.send_raw(txn)
        
    def morph_axie(self, axie_id):
        sign_msg = self.sign("axie_id=%d&owner=%s"%(axie_id, self.addr))
        info = self.get_axie_info(axie_id)
        if time.time() - info['birthDate'] < 5*24*60*60:
            raise BotError("Cant morph to adult now")
            
        if info['owner'] != self.addr:
            raise BotError("This is NOT your axie")
            
        if info['stage'] == 4:
            raise BotError("Axie already adult")
            
        reqData = {"operationName":"MorphAxie","variables":{"axieId":"%d"%axie_id, "owner":self.addr,"signature":sign_msg.signature.hex()},"query":"mutation MorphAxie($axieId: ID!, $owner: String!, $signature: String!) {\n  morphAxie(axieId: $axieId, owner: $owner, signature: $signature)\n}\n"}
        resp = self.send_req(CONFIG.marketql, reqData)
        return resp['data']['morphAxie']
        
    def sell_axie(self, axie_id, min_value, max_value, max_days):
        min_value = Web3.toWei(min_value, 'ether')
        max_value = Web3.toWei(max_value, 'ether')
        toSec = max_days*60*60*24
        
        info = self.get_axie_info(axie_id)
        if info['owner'] != self.addr:
            raise BotError("This is NOT your axie")
            
        txn = market_contract.functions.createAuction([1], [CONFIG.contracts["axies"]], [axie_id], [min_value], [max_value], [CONFIG.contracts["ronin"]], [toSec])
        return self.send_raw(txn)
        
    def send(self, to_addr, value, type):
        balance = 0
        contract = None
        if type == "ETH":
            balance = Web3.toWei(self.balance(), 'ether')
            contract = ronin_contract
            value = Web3.toWei(value, 'ether')
        elif type == "SLP":
            balance = self.slp_balance()["value"]
            contract = slp_contract
            value = int(value)
        elif type == "AXS":
            balance = self.axs_balance()
            contract = axs_contract
            value = int(value)
        else:
            raise BotError("Unknown type")
            
        if value > balance:
            raise BotError("Not enough money")
            
        to_addr = Web3.toChecksumAddress(to_addr)
        txn = contract.functions.transfer(to_addr, value)
        return self.send_raw(txn)
    
    def axs_balance(self):
        data = axs_contract.functions.balanceOf(Web3.toChecksumAddress(self.addr)).buildTransaction({'gas': 1000000, 'gasPrice': 0})
        resp = common_eth.call(data)
        return Web3.fromWei(int(HexBytes(resp).hex(), 16), 'ether')
        
    def slp_balance(self):
        slp_info = self.get_slp_info()
        
        ret = {"value": 0, 'allow': False, 'claimable': 0}
        if 'blockchain_related' in slp_info:
            ret['value'] = slp_info['blockchain_related']["balance"] or 0
            
            if 'signature' in slp_info['blockchain_related'] and slp_info['blockchain_related']['signature']:
                ret['claimable'] = slp_info['blockchain_related']['signature']['amount'] - slp_info['blockchain_related']['checkpoint']
                ret['allow'] = (time.time() - slp_info['last_claimed_item_at'] >= 14*24*60*60) or ret['claimable'] != 0
                
        return ret
        
    def breed_slp_price(self, axie_id):
        txn = axies_contract.functions.getRequirementsForBreeding(axie_id)
        txn = txn.buildTransaction({'gas': 1000000, 'gasPrice': 0}) 
        resp = common_eth.call(txn)
        return Web3.fromWei(int(HexBytes(resp).hex(), 16), 'ether')
        
    def breed_axs_price(self):
        txn = axies_contract.functions.breedingFee()
        txn = txn.buildTransaction({'gas': 1000000, 'gasPrice': 0})
        resp = common_eth.call(txn)
        return Web3.fromWei(int(HexBytes(resp).hex(), 16), 'ether')
    
    def get_axies(self):
        if not self.auth:
            self.login_market()
            
        reqData = {"operationName":"GetAxieBriefList","variables":{"from":0,"size":24,"sort":"IdDesc","auctionType":"All","owner":self.addr,"criteria":{"region":None,"parts":None,"bodyShapes":None,"classes":None,"stages":None,"numMystic":None,"pureness":None,"title":None,"breedable":None,"breedCount":None,"hp":[],"skill":[],"speed":[],"morale":[]}},"query":"query GetAxieBriefList($auctionType: AuctionType, $criteria: AxieSearchCriteria, $from: Int, $sort: SortBy, $size: Int, $owner: String) {\n  axies(auctionType: $auctionType, criteria: $criteria, from: $from, sort: $sort, size: $size, owner: $owner) {\n    total\n    results {\n      ...AxieBrief\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment AxieBrief on Axie {\n  id\n  name\n  stage\n  class\n  breedCount\n  image\n  title\n  battleInfo {\n    banned\n    __typename\n  }\n  auction {\n    currentPrice\n    currentPriceUSD\n    __typename\n  }\n  parts {\n    id\n    name\n    class\n    type\n    specialGenes\n    __typename\n  }\n  __typename\n}\n"}
        jData = self.send_req(CONFIG.marketql, reqData)
        axies = jData['data']['axies']
        return axies['results']
        
    def breed(self, axie_id1, axie_id2):
        if self.slp_balance()['value'] < self.breed_slp_price(axie_id1) + self.breed_slp_price(axie_id2):
            raise BotError("Not enough SLP")
        
        if self.axs_balance() < self.breed_axs_price():
            raise BotError("Not enough AXS")
            
        txn = axies_contract.functions.breedAxies(axie_id1, axie_id2)
        return self.send_raw(txn)
        
class CONFIG(object):
    free_rpc = 'https://proxy.roninchain.com/free-gas-rpc'
    common_rpc = "https://api.roninchain.com/rpc"
    marketql = "https://graphql-gateway.axieinfinity.com/graphql"
    contracts = {
        "ronin": Web3.toChecksumAddress("0xc99a6a985ed2cac1ef41640596c5a5f9f4e19ef5"),
        "market": Web3.toChecksumAddress("0x213073989821f738a7ba3520c3d31a1f9ad31bbd"),
        "axies": Web3.toChecksumAddress("0x32950db2a7164ae833121501c797d79e7b79d74c"),
        "slp": Web3.toChecksumAddress("0xa8754b9fa15fc18bb59458815510e40a12cd2014"),
        "axs": Web3.toChecksumAddress("0x97a9107c1793bc407d6f527b77e7fff4d812bece")
    }
    _id = 0
    acc_id = 1

free_eth   = Web3(HTTPProvider(CONFIG.free_rpc)).eth
common_eth = Web3(HTTPProvider(CONFIG.common_rpc)).eth
ronin_contract = free_eth.contract(address=CONFIG.contracts['ronin'], abi=json.loads(open('ronin_eth.json').read()))
market_contract = free_eth.contract(address=CONFIG.contracts['market'], abi=json.loads(open('market_abi.json').read()))
axies_contract = free_eth.contract(address=CONFIG.contracts['axies'], abi=json.loads(open('axies_abi.json').read()))
slp_contract = free_eth.contract(address=CONFIG.contracts['slp'], abi=json.loads(open('slp_abi.json').read()))
axs_contract = free_eth.contract(address=CONFIG.contracts['axs'], abi=json.loads(open('axs_abi.json').read()))
