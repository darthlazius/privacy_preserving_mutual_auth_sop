from flask import Flask, request, jsonify
import hashlib
import secrets
import time
import json

app = Flask(__name__)
r3 = secrets.token_hex(16)  # Random number
K_rc = secrets.token_hex(32)  # RC's secret key
user_database = {}  
server_database = {}  

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Registration Center"}), 200

@app.route('/register_server', methods=['POST'])
def register_server():
    data = request.get_json()
    ID_j = data.get('ID_j')
    P_j = data.get('P_j')
    Q_j = data.get('Q_j')
    Loc_j = data.get('Loc_j')

    if not all([ID_j, P_j, Q_j, Loc_j]):
        return jsonify({"error": "Missing server parameters"}), 400
    
    print(f"Registering server: {ID_j}, {P_j}, {Q_j}, {Loc_j}")

    if ID_j in server_database:
        return jsonify({"error": "Server ID already exists"}), 409
    
    SRT_j = str(time.time())  # Server registration timestamp
    SSK_j = hashlib.sha256((K_rc + P_j + SRT_j).encode()).hexdigest()
    print(f"SSK_j: {SSK_j}")
    
    server_database[ID_j] = {"SSK_j": SSK_j, "Q_j": Q_j, "Loc_j": Loc_j}
    print(f"Server registered: {ID_j}")
    return jsonify({"SSK_j": SSK_j}), 201



@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.get_json()
    UID_i = data.get('UID_i')
    A_i = data.get('A_i')

    if not all([UID_i, A_i]):
        return jsonify({"error": "Missing user parameters"}), 400
    USK_i = hashlib.sha256((UID_i+K_rc+r3).encode()).hexdigest()
    print(f"This is the user session key{USK_i}")
    temp_1 = hashlib.sha256((K_rc+r3+A_i).encode()).hexdigest()
    temp_2 = hashlib.sha256((UID_i+A_i).encode()).hexdigest()
    c_i_int = int(temp_1, 16) ^ int(temp_2, 16) ^int(USK_i, 16)
    C_i = hex(c_i_int)[2:].zfill(64)
    D_i = hex(int(A_i, 16) ^ int(USK_i, 16))[2:].zfill(64)
    print(f"This is the D_i:{D_i}")
    List_sJ = [(ID_j +server['SSK_j']+server['Loc_j']) for ID_j, server in server_database.items()]
    user_database[UID_i] = {"C_i":C_i} 

    print(f"User registered: {UID_i}")
    SC_i = {"C_i":C_i, "D_i":D_i, "List_sJ":List_sJ}
    return jsonify(SC_i), 201

@app.route('/get_server', methods=['GET'])
def get_server():
    return jsonify(server_database), 200



if __name__ == '__main__':
    app.run(port=5000, debug=True)