from flask import Flask, request, jsonify
import hashlib
import secrets
import time
import requests
import json
import os

app = Flask(__name__)

RC_URL = os.environ.get("RC_URL", "http://localhost:5000")
ID_j = os.environ.get("SERVER_ID", "hospital2")
PW_j = os.environ.get("SERVER_PASSWORD", "admin1234")
Loc_j = os.environ.get("SERVER_LOCATION", "Goa")
r_S = secrets.token_hex(16)
SSK_j = None

def calculate_P_j():
    return hashlib.sha256((ID_j + r_S + PW_j).encode()).hexdigest()

def calculate_Q_j(P_j):
    h1 = hashlib.sha256((ID_j + PW_j).encode()).hexdigest()
    h2  = int(h1, 16) ^ int(P_j, 16)
    return hex(h2)[2:].zfill(64)

def xor_hex_strings(hex_str1, hex_str2):
    int_val = int(hex_str1, 16) ^ int(hex_str2, 16)
    return hex(int_val)[2:].zfill(64)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the server ",
                    "creds":{
                        "ID_j": ID_j,
                        "PW_j": PW_j,
                        "Loc_j": Loc_j
                    }}), 200

@app.route('/register_server', methods=['POST'])
def register_server():
    P_j = calculate_P_j()
    Q_j = calculate_Q_j(P_j)
    data = {
        "ID_j": ID_j,
        "P_j": P_j,
        "Q_j": Q_j,
        "Loc_j": Loc_j
    }
    try:
        response = requests.post(f"{RC_URL}/register_server", json=data)
        response.raise_for_status()
        result = response.json()
        global SSK_j
        SSK_j = result.get('SSK_j')
        if SSK_j:
            print(f"Server registered. SSK_j:{SSK_j}")
            return jsonify({"message": "Server registered"}), 200
        else:
            print("Server registration failed")
            return jsonify({"error": "Server registration failed"}), 500
    except requests.exceptions.RequestException as e:
        print(f"Error registering with RC: {e}")
        return jsonify({"error": f"Registration failed: {e}"}), 500

@app.route('/authenticate', methods=['POST'])
def authenticate_user():
    data = request.get_json()
    alpha_i = data.get("alpha_i")
    beta_i = data.get("beta_i")
    T1 = data.get("T1")
    UID_i = data.get("UID_i")
    C_i = data.get("C_i")  # VERY IMPORTANT: Get C_i from the client

    if not all([alpha_i, beta_i, T1, UID_i, C_i]):  # Check for C_i too
        return jsonify({"error": "Missing parameters"}), 400

    # 3. Server receives and verifies
    delta_T = 10  # Example
    T2 = str(time.time())
    if float(T2) - float(T1) > delta_T:
        return jsonify({"error": "Authentication failed: Timestamp expired"}), 400

    UID_i_prime = xor_hex_strings(hashlib.sha256((ID_j + str(SSK_j) + T1).encode()).hexdigest(), alpha_i)
    beta_i_prime = hashlib.sha256((UID_i_prime + str(SSK_j) + C_i + T1).encode()).hexdigest()

    if beta_i_prime != beta_i:
        return jsonify({"error": "Authentication failed: Invalid request"}), 401

    # 4. Server calculates and sends response
    VT_ij = secrets.token_hex(16)  
    gamma_i = xor_hex_strings((VT_ij + Loc_j).encode('utf-8').hex(), hashlib.sha256((C_i + UID_i_prime + ID_j + beta_i_prime).encode()).hexdigest())
    sigma_i = hashlib.sha256((VT_ij + C_i + str(float(T2) - float(T1))).encode()).hexdigest() #Convert to string before hashing
    #hashing expects string as the input but you are providing float

    return jsonify({"gamma_i": gamma_i, "sigma_i": sigma_i, "T2": T2, "VT_ij": VT_ij, "Loc_j": Loc_j}), 200



if __name__ == '__main__':
    # Attempt registration on startup (only if not already registered)
    if not SSK_j:
        with app.app_context():
            response = requests.post("http://localhost:5001/register_server") #Register with RC
            if response.status_code != 200:
                print ("There was an error reaching the server. Check the server URL")
            else:
                print ("There was a server. Registration Successful")

    app.run(port=5001, debug=True)
