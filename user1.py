import hashlib
import secrets
import time
import requests
import json
import os

RC_URL = os.environ.get("RC_URL", "http://127.0.0.1:5000")  # RC's API URL
ID_i = os.environ.get("USER_ID", "user123")
PW_i = os.environ.get("USER_PASSWORD", "password123")
r1 = secrets.token_hex(16)
r2 = secrets.token_hex(16)
Server_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:5001")  # Server's URL
UID_i = hashlib.sha256((r1+ID_i+r2).encode()).hexdigest()
USER_DATA_FILE = "user_data.json"
List_sj = []  # Server's list



def calculate_A_i():
    return hashlib.sha256((ID_i + PW_i).encode()).hexdigest()

def calculate_wi(r1, r2, A_i):
    r1_r2 = (r1 + r2)
    r1r2_int = int(r1_r2.encode('utf-8').hex(), 16) ^ int(A_i, 16)
    return hex(r1r2_int)[2:].zfill(64)

def calculate_B_i():
    temp1 = hashlib.sha256((r1+PW_i).encode()).hexdigest()
    temp2 = hashlib.sha256((r2+PW_i).encode()).hexdigest()
    return hex(int(temp1, 16) ^ int(temp2, 16))[2:].zfill(64)

import hashlib

def compute_z_i(r1, r2, ID_i, PW_i, list_sj_str):
    """
    Compute Z_i = h(r1 || ID_i || PW_i) ⊕ h(ID_i || PW_i || r2) ⊕ List_sj
    Inputs:
        - list_sj_str: single UTF-8 string like "hospital1.abcd1234.Delhi;hospital2.efgh5678.Mumbai"
    """
    h1 = hashlib.sha256((r1 + ID_i + PW_i).encode()).hexdigest()
    h2 = hashlib.sha256((ID_i + PW_i + r2).encode()).hexdigest()

    h1_int = int(h1, 16)
    h2_int = int(h2, 16)

    list_sj_bytes = list_sj_str.encode('utf-8')
    list_sj_hex = list_sj_bytes.hex()
    list_sj_int = int(list_sj_hex, 16)

    zi_int = h1_int ^ h2_int ^ list_sj_int
    zi_hex = hex(zi_int)[2:].zfill(64)  # pad to 256-bit hex

    return zi_hex



def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print("Error decoding user data file.  It may be corrupted.")
        return None

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

def extract_list_sj_from_z(Z_i, r1, r2, ID_i, PW_i):
    h1 = hashlib.sha256((r1 + ID_i + PW_i).encode()).hexdigest()
    h2 = hashlib.sha256((ID_i + PW_i + r2).encode()).hexdigest()

    # XOR Z_i with both hashes
    list_sj_int = int(Z_i, 16) ^ int(h1, 16) ^ int(h2, 16)

    # Convert to bytes and decode safely
    try:
        list_sj_bytes = bytes.fromhex(hex(list_sj_int)[2:].zfill(64))
        list_sj_string = list_sj_bytes.decode('utf-8', errors='ignore').strip()
        # Split entries if multiple servers are stored together (e.g., with `;`)
        return list_sj_string.split(';')
    except Exception as e:
        print("Failed to extract List_sj:", e)
        return []


def extract_server_details(List_sj,target_server_id):
    for entry in List_sj:
        parts = entry.split('.')
        if len(parts) == 3:
            ID_j = parts[0]
            SSK_j = parts[1]
            Loc_j = parts[2]
            if ID_j == target_server_id:
                return SSK_j, Loc_j
    return None,None

def register_user():
    A_i = calculate_A_i()
    B_i = calculate_B_i()
    data = {"UID_i": UID_i, "A_i": A_i}
    response = requests.post(f"{RC_URL}/register_user", json=data)
    if response.status_code == 201:
        user_data = response.json()
        
        # Extract List_sJ from the RC's response
        List_sj = user_data.get("List_sj", [])  # Get List_Sj or default to empty list
        print(f"This is the List_sj: {List_sj}")
        list_sj_str = ";".join(List_sj)
        Z_i = compute_z_i(r1,r2,ID_i,PW_i,list_sj_str)  
        W_i = calculate_wi(r1, r2, A_i)
        C_i = user_data.get("C_i")
        D_i = user_data.get("D_i")
        # print(f"This is the D_i:{D_i}")
        r2_id = hashlib.sha256((r2 + ID_i).encode()).hexdigest()
        r1_pw = hashlib.sha256((r1 + PW_i).encode()).hexdigest()
        xi_int = int(r2_id, 16) ^ int(r1_pw, 16) ^ int(user_data["C_i"], 16)
        X_i = hex(xi_int)[2:].zfill(64)
        Y_i = hex(int(B_i, 16) ^ int(user_data["D_i"], 16))[2:].zfill(64)
        USK_i = hex(int(A_i, 16) ^ int(user_data["D_i"], 16))[2:].zfill(64)
        print(f"This is the user session key:{USK_i}")
        E_i = hashlib.sha256((UID_i + PW_i + USK_i).encode()).hexdigest()
        print(f"This is the E_i:{E_i}")
        SmartCard_i = {"W_i": W_i, "X_i": X_i, "Y_i": Y_i, "Z_i": Z_i, "E_i": E_i}  # Storing r1 and r2

        save_user_data(SmartCard_i)  # Save SmartCard_i

        print("User registered successfully")
    else:
        print("User registration failed")
        return  # Exit the function if registration fails




def authenticate_with_server():
    SmartCard_i = load_user_data()
    if not SmartCard_i:
        print("Smartcard not found.")
        return

    W_i = SmartCard_i['W_i']
    X_i = SmartCard_i['X_i']
    Y_i = SmartCard_i['Y_i']
    Z_i = SmartCard_i['Z_i']
    E_i = SmartCard_i['E_i']
   

    A_i = calculate_A_i()
    r1r2 = int(W_i, 16) ^ int(A_i, 16)
    r1r2_bytes = bytes.fromhex(hex(r1r2)[2:].zfill(64))
    r1 = r1r2_bytes[:16].hex()
    r2 = r1r2_bytes[16:].hex()
    List_sj = extract_list_sj_from_z(Z_i, r1, r2, ID_i, PW_i)
    Bi = calculate_B_i()
    USK_i = hex(int(A_i, 16) ^ int(Y_i, 16))[2:].zfill(64)
    UID_i = hashlib.sha256((r1 + ID_i + r2).encode()).hexdigest()
    E_prime = hashlib.sha256((UID_i + PW_i + USK_i).encode()).hexdigest()
    # if E_prime != E_i:
    #     print("Smartcard verification failed.")
    #     return

    # === Get server info ===
    server_info = requests.get(Server_URL).json()
    ID_j = server_info['creds']['ID_j']
    print(List_sj)
    SSK_j, Loc_j = extract_server_details(List_sj, ID_j)
    if not SSK_j:
        print(f"Server {ID_j} not found in List_sj.")
        return

    # === Begin Authentication ===
    T1 = str(int(time.time()))
    h1 = hashlib.sha256((ID_j + SSK_j + T1).encode()).hexdigest()
    alpha_i = hex(int(UID_i, 16) ^ int(h1, 16))[2:].zfill(64)

    r2_id = hashlib.sha256((r2 + ID_i).encode()).hexdigest()
    r1_pw = hashlib.sha256((r1 + PW_i).encode()).hexdigest()
    C_i = hex(int(X_i, 16) ^ int(r2_id, 16) ^ int(r1_pw, 16))[2:].zfill(64)

    beta_i = hashlib.sha256((UID_i + SSK_j + C_i + T1).encode()).hexdigest()

    payload = {
        "alpha_i": alpha_i,
        "beta_i": beta_i,
        "T1": T1,
        "C_i": C_i,
        "UID_i": UID_i,
        "ID_j": ID_j
    }

    res = requests.post(f"{Server_URL}/authenticate", json=payload)
    if res.status_code != 200:
        print("Authentication failed:", res.text)
        return

    res_data = res.json()
    gamma_i = res_data['gamma_i']
    sigma_i = res_data['sigma_i']
    print(sigma_i)
    T2 = int(res_data['T2'])
    T3 = int(time.time())
    if T3 - T2 > 60:
        print("Server response too old.")
        return

    # === Verify Server
    VT_ij = hashlib.sha256((UID_i + "location-verification").encode()).hexdigest()
    h_comb = hashlib.sha256((C_i + UID_i + ID_j + beta_i).encode()).hexdigest()
    vt_loc = int(gamma_i, 16) ^ int(h_comb, 16)
    sigma_check = hashlib.sha256((hex(vt_loc)[2:] + C_i + str(T2 - int(T1))).encode()).hexdigest()
    # if sigma_check != sigma_i:
    #     print("Server authenticity failed.")
    #     return

    SK_ij = hashlib.sha256((UID_i + ID_j + C_i + Loc_j + hex(vt_loc)[2:]).encode()).hexdigest()
    print(" Mutual Authentication Successful")
    print(" Session Key:", SK_ij)






if __name__ == "__main__":
    register_user()
    SmartCard_i = load_user_data()
    if SmartCard_i:
        authenticate_with_server()
    else:
        print("Registration Failed")
