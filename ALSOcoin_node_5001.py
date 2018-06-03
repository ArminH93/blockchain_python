#Create a Cryotcurrency

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#Build a Blockchain

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set() # initialize empty set
    
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash' : previous_hash,
                 'transactions' : self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            # CHECK Nr.1: Wird ein kryptografischer Hash-Wert retourniert, welcher mit 0000 anfängt, wurde das "problem" gelöst.
            
            # CHECK Nr.2: Überprüft, ob der previous_hash von jedem Block derselbe ist, wie der Hash-Wert vom vorherigen Block.
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000': # Überprüft, ob die ersten 4 Stellen den Wert '0' haben.
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        # Formatiert den Wert, sodass SHA-256 diesen akzeptiert.
        encoded_block = json.dumps(block, sort_keys = True).encode() 
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0] # Erster Block in der Chain
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            # the chain is not valid, if the previous_hash of current block is different than the hash of the previous block
            if block['previous_hash'] != self.hash(previous_block):
                return False
            # check if proof of each block is valid. Meaning, if it solves the problem. 
            # Compare the proof of current block with the proof of the previous block
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender' : sender,
                                'receiver' : receiver,
                                'amount' : amount})
        # holt den letzten block + 1 damit der im aktuellen Block die Transaktion hinterlegt wird und nicht beim vorherigen Block.
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for nodes in network:
            # find the largest chain
            response = requests.get(f'http://{nodes}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain: # if longest chain is NOT NONE
            self.chain = longest_chain
            return True
        return False


# CREATING A WEB APP
app = Flask(__name__)

# Create an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# CREATING A BLOCKCHAIN
blockchain = Blockchain()

# MINING A NEW BLOCK
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    #current proof which will be added to the next block
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'Armin', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congrats, you just mined a block!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions' : block['transactions']}
    return jsonify(response), 200 #200 = http status code => OK


# GETTING THE FULL BLOCKCHAIN
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    #will be displayed when the get request happens
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'All good. The Blockchain is valid.'}
    else:
        response = {'message' : 'There is a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount']) # Getting the value of the keys
    response = {'message' : f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

# Decentralizing Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All nodes are connected. The ALSOcoin BLockchain now contains the following nodes: ' ,
                'total_nodes' : list(blockchain.nodes)}
    return jsonify(response)

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : 'The nodes had different chains so the chain was replaced by the longest one.', 
                    'new_chain' : blockchain.chain}
    else:
        response = {'message' : 'All good. The chain is the largest one.',
                    'actual_chain' : blockchain.chain}
    return jsonify(response), 200


app.run(host = '0.0.0.0', port = 5001)