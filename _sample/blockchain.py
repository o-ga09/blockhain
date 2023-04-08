# coding :utf-8
from hashlib import sha256
from flask import Flask,request
import requests 
import datetime as date
import json

#ブロックの本体
class Block :
    #ブロックの中身
    def __init__(self,index,timestamp,data,previous_hash) :
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
    #ハッシュを作る
    def create_hash(self) :
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
#ブロックチェーンを作る
class BlockChain :
    def __init__(self) :
        self.unconfirmed_data = [] #ブロックチェーンに格納されていないデータ
        self.chain = []
        self.create_genesis_block()
    #ジェネシスブロックを作る
    def create_genesis_block(self) :
        genesis_block = Block(0,[],date.datetime.now(),"0")
        genesis_block.hash = genesis_block.create_hash()
        self.chain.append(genesis_block)
    @property#読み取りのみ(一個前のブロック)
    def last_block(self) :
        return self.chain[-1]
    #プルーフオブワークの難易度(計算の)
    difficulty = 2
    #プルーフオブワークをする
    def proof_of_work(self,block) :

        block.nonce = 0

        compute_hash = block.create_hash()
        while not compute_hash.startswith('0' * BlockChain.difficulty) :
            block.nonce += 1
            compute_hash = block.create_hash()
        
        return compute_hash
    #ブロックを追加する
    def add_block(self,block,proof) :
        previous_hash = self.last_block.hash
        
        if previous_hash != block.previous_hash : #前のハッシュと現在のブロックのハッシュが同じでないとだめ
            return False
        if not self.is_Valid_proof(block,proof) : #ナンス値を満たすかどうか
            return False
        block.hash = proof
        self.chain.append(block)
        return True
    #ハッシュがナンスを満たすかどうか識別
    def is_Valid_proof(self,block,block_hash) :
        return (block_hash.startswith('0' * BlockChain.difficulty) and block_hash == block.create_hash())
    #まだ追加されていないデータをリストに取りあえず追加
    def add_new_transaction(self,transaction) :
        self.unconfirmed_data(transaction)
    #採掘
    def mine(self) :
        if not self.unconfirmed_data :
            return False
        last_block = self.last_block
        new_block = Block(index=last_block.index + 1,
                           data=self.unconfirmed_data,
                           timestamp=date.datetime.now(),
                           previous_hash=last_block.hash)
        proof = self.proof_of_work(new_block)
        self.add_block(new_block,proof)
        self.unconfirmed_data = []
        return new_block.index
#####################################################ここまでブロックチェーンの構築
#ここからインターフェースの構築
app = Flask(__name__)
#ブロックチェーンのコピーを作成
blockchain = BlockChain()
#Weｂ上から使えるようにするために
@app.route('/new_transaction',methods=['POST'])
def new_transaction() :
    text_fields = request.get_json()
    required_fields = ["suthor","content"]

    for field in required_fields :
        if not text_data.get(field) :
            return "Invalid transaction data",404
    text_data["timestamp"] = date.datetime.now()
    blockchain.add_new_transaction(text_data)
    return "Success",201
@app.route('/chain',methods=['GET'])
def get_chain() :
     chain_data = []
     for block in blockchain.chain :
         chain_data.append(block.__dict__)
     return json.dumps({"length" : len(chain_data),
                     "chain" : chain_data})
@app.route('/mine',methods=['GET'])
def mine_unconfirmed_transaction() :
     result = blockchain.mine()
     if not result :
         return "No transaction to mine!!!"
     return "Block #{} is mined.".format(result)
@app.route('/pending_tx')
def get_pending_tx() :
     return json.dumps(blockchain.unconfirmed_data)
###################ブロックチェーンの参加者######################################
peers = set()
###################参加者の追加#################################################
@app.route('/add_nodes',methods=['POST'])
def register_new_peer() :
     nodes = request.get_json()
     if not nodes :
         return "Invalid data", 400
     for node in nodes :
         peers.add(node)
     return "Success", 201
################コンセンサスアルゴリズムの追加(合意形成)##########################
def consensus() : 
    global blockchain
    
    longest_chain = None                 #一番長いチェーンの長さ
    current_len = len(blockchain)        #現在のチェーンの長さ

    for node in peers :
        response = requests.get('https://{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validly(chain) :
            current_len = length
            longest_chain = chain 
    if longest_chain :
        blockchain = longest_chain 
        return True 
    return False
#####################################他の人が参加するチェーンにブロックを追加する########
@app.route('/add_block',methods=['POST'])
def validate_and_add_block() :  #ブロックの追加と正しいかどうかの確認
     block_data = request.get_json()
     block = Block(block_data["index"],block_data["data"],block_data["timestamp"],block_data["previous_hash"])
     proof = block_data['hash']
     added = blockchain.add_block(block,proof)

     if not added :
         return "The block was discarded by the node", 400
     return "Block added to the chain", 201
def announce_new_block(block) : #チェーンにブロックが追加されたことを他の人に知らせる
     for peer in peers :
         url = "htpp://{}/add_block".format(peer)
         requests.post(url,data=json.dumps(block.__dict__,sort_key=True))
@app.route('/register_node',methods=['POST'])
def register_new_peers() : #参加者の追加
     node_addess = request.get_json()["node_addess"]
     if not node_addess :
         return "Invalid data", 400
     peers.add(node_addess)
     return get_chain()
@app.route('/register_with',methods=['POST'])
def register_with_existing_node() : #トランザクションの追加
     node_address = request.get_json()["node_adddess"]
     if not node_addess :
         return "Invalid data", 400
     data = {"node_addess" : request.host_url}
     headers = {'Content-Type' : "application/json"}

     response = requests.post(node_addess + "/register_node", data=json.dumps(data),headers=headers)
     if response.status_code == 200 :
         global blockchain
         global peers 
         chain_dump = response.json()['chain']
         blockchain = create_chain_from_dump(chain_dump)
         peers.update(response.json()['peers'])
         return "Registration successful", 200
     else :
         return response.content, response.status_code 
def create_chain_from_dump(chain,_dump) : #json形式からブロックを作る。
     blockchain = BlockChain()
     for idx, block_data in enumerate(chain_dump) :
         block = Block(block_data["index"],
                        block_data["data"],
                        block_data["timestamp"],
                        block_data["previoius_hash"])
         proof = block_data['hash']
         if idx > 0 :
             added = blockchain.add_block(block,proof)
             if not added :
                 raise Exception("The chain dump is tampered!")
         else :
             blockchain.chain.append(block)
     return blockchain 