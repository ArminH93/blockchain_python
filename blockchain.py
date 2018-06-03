#Create a Blockchain

import datetime
import hashlib
import json
from flask import Flask, jsonify

#Build a Blockchain

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0')
    
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash' : previous_hash}
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
        previous_block = chain[0] # Erster Block in der Chain.
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            # Die Chain ist ungültig, wenn der previous_hash des aktuellen Blocks anders ist, als der vorherige Block.
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True


# CREATING A WEB APP
app = Flask(__name__)

# CREATING A BLOCKCHAIN
blockchain = Blockchain()

# MINING A NEW BLOCK
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    # Aktueller proof, der beim nächsten Block hinzugefügt wird.
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congrats, you just mined a block!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash']}
    return jsonify(response), 200 #200 = http status code => OK


# GETTING THE FULL BLOCKCHAIN
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    # Wird dargestellt, wenn die Anfrage (request) passiert.
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



app.run(host = '0.0.0.0', port = 5000)