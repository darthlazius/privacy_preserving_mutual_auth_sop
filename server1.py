from flask import Flask, request, jsonify
import hashlib
import secrets
import time
import requests
import json
import os
import sqlite3
app = Flask(__name__)


def init_server_db():
    conn = sqlite3.connect('server.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS servers(
                ID_j TEXT PRIMARY KEY,
                SSK_j TEXT,
                Loc_j TEXT,
                Q_j TEXT)''')
    conn.commit()
    conn.close()




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
    C_i = data.get("C_i")
    UID_i = data.get("UID_i")
    ID_j_received = data.get("ID_j")

    if ID_j_received != ID_j:
        return jsonify({"error": "Invalid Server ID"}), 403
    
    T2 = str(int(time.time()))
    # Step 1: Recompute UID_i from alpha
    cursor = sqlite3.connect('rc.db').cursor()
    SSK_j = cursor.execute("SELECT SSK_j FROM servers WHERE ID_j = ?", (ID_j,)).fetchone()
    SSK_j = SSK_j[0] if SSK_j else None
    print(SSK_j)
    h_val = hashlib.sha256((ID_j + SSK_j + T1).encode()).hexdigest()
    UID_i_recovered = hex(int(alpha_i, 16) ^ int(h_val, 16))[2:].zfill(64)

    beta_check = hashlib.sha256((UID_i_recovered + SSK_j + C_i + T1).encode()).hexdigest()
    if beta_check != beta_i:
        return jsonify({"error": "β_i mismatch"}), 403

    VT_ij = hashlib.sha256((UID_i_recovered + "location-verification").encode()).hexdigest()
    h_comb = hashlib.sha256((C_i + UID_i_recovered + ID_j + beta_i).encode()).hexdigest()
    gamma_i = hex(int(VT_ij + Loc_j.encode().hex(), 16) ^ int(h_comb, 16))[2:].zfill(64)
    sigma_i = hashlib.sha256((VT_ij + C_i + str(int(T2) - int(T1))).encode()).hexdigest()

    return jsonify({
        "gamma_i": gamma_i,
        "sigma_i": sigma_i,
        "T2": T2
    }), 200



@app.route('/update_server_db', methods=['POST'])
def update_server_db():
    T = str(int(time.time()))
    data = {
        "ID_j": ID_j,
        "T": T
    }

    try:
        response = requests.post(f"{RC_URL}/update_server_db", json=data)
        if response.status_code == 200:
            return jsonify({"message": "Server record updated with RC"}), 200
        else:
            return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Failed to contact RC: {e}"}), 500


if __name__ == '__main__':
    # Attempt registration on startup (only if not already registered)
    if not SSK_j:
        with app.app_context():
            response = requests.post("http://localhost:5000/register_server") #Register with RC
            if response.status_code != 200:
                print ("There was an error reaching the server. Check the server URL")
            else:
                print ("There was a server. Registration Successful")

    app.run(port=5001, debug=True)
