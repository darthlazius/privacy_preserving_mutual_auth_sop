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
Server_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:5000")  # Server's URL
UID_i = hashlib.sha256((r1+ID_i+r2).encode()).hexdigest()
USER_DATA_FILE = "user_data.json"
List_sJ = []  # Server's list
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

def calculate_zi(r1, ID_i, PW_i, List_Sj, ID_i2, PW_i2, r2):
    h1 = hashlib.sha256((r1 + ID_i + PW_i).encode()).hexdigest()
    h2 = hashlib.sha256((ID_i2 + PW_i2 + r2).encode()).hexdigest()
    
    # Check if List_Sj is empty
    if not List_Sj:
        combined_list_sj = ''  # Or some other default value
    else:
        combined_list_sj = ''.join([item[0] + item[1] + item[2] for item in List_Sj])
    
    # Check for empty string before converting to int
    if combined_list_sj:
        zi_int = int(combined_list_sj.encode('utf-8').hex(), 16) ^ int(h1, 16) ^ int(h2, 16)
        return hex(zi_int)[2:].zfill(64)
    else:
        # Handle the case where combined_list_sj is empty
        zi_int = int(h1, 16) ^ int(h2, 16)
        return hex(zi_int)[2:].zfill(64)


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

def register_user():
    A_i = calculate_A_i()
    B_i = calculate_B_i()
    data = {"UID_i": UID_i, "A_i": A_i}
    response = requests.post(f"{RC_URL}/register_user", json=data)
    if response.status_code == 201:
        user_data = response.json()
        
        # Extract List_sJ from the RC's response
        List_sJ = user_data.get("List_Sj", [])  # Get List_Sj or default to empty list

        W_i = calculate_wi(r1, r2, A_i)
        C_i = user_data.get("C_i")
        D_i = user_data.get("D_i")

        r2_id = hashlib.sha256((r2 + ID_i).encode()).hexdigest()
        r1_pw = hashlib.sha256((r1 + PW_i).encode()).hexdigest()
        xi_int = int(r2_id, 16) ^ int(r1_pw, 16) ^ int(user_data["C_i"], 16)
        X_i = hex(xi_int)[2:].zfill(64)
        Y_i = hex(int(B_i, 16) ^ int(user_data["D_i"], 16))[2:].zfill(64)
        USK_i = hex(int(A_i, 16) ^ int(user_data["D_i"], 16))[2:].zfill(64)
        E_i = hashlib.sha256((UID_i + USK_i + PW_i).encode()).hexdigest()
        Z_i = calculate_zi(r1, ID_i, PW_i, List_sJ, ID_i, PW_i, r2)
        SmartCard_i = {"UID_i": UID_i, "A_i": A_i, "B_i": B_i, "W_i": W_i, "X_i": X_i, "Y_i": Y_i, "Z_i": Z_i, "E_i": E_i, "List_sJ": List_sJ, "r1": r1, "r2": r2}  # Storing r1 and r2

        save_user_data(SmartCard_i)  # Save SmartCard_i

        print("User registered successfully")
    else:
        print("User registration failed")
        return  # Exit the function if registration fails

def authenticate_with_server():
    SmartCard_i = load_user_data()  # Load smart card data
    if not SmartCard_i:
        print("User data not found. Please register first.")
        return

    # Extract values from smart card
    W_i = SmartCard_i["W_i"]
    X_i = SmartCard_i["X_i"]
    Y_i = SmartCard_i["Y_i"]
    Z_i = SmartCard_i["Z_i"]
    E_i = SmartCard_i["E_i"]

    # 1. User Computations
    hash_idpw = hashlib.sha256((ID_i + PW_i).encode()).hexdigest()
    r1r2 = hex(int(W_i, 16) ^ int(hash_idpw, 16))[2:].zfill(64)
    USK_i = hex(int(calculate_A_i(), 16) ^ int(Y_i, 16) ^ int(calculate_B_i(), 16))[2:].zfill(64)
    E_i_prime = hashlib.sha256((UID_i + PW_i + USK_i).encode()).hexdigest()

    if E_i_prime != E_i:
        print("Authentication failed: Invalid credentials")
        return

    # 2. Prepare and Send Request to Server
    if not List_sJ:
        print("No servers registered. Cannot authenticate.")
        return

    ID_j = List_sJ[0][0]
    SSK_j = List_sJ[0][1]
    C_i = hex(int(X_i, 16) ^ int(hashlib.sha256((r2 + ID_i).encode()).hexdigest(), 16) ^ int(hashlib.sha256((r1 + PW_i).encode()).hexdigest(), 16))[2:].zfill(64)
    T1 = str(time.time())
    alpha_i = hex(int(hashlib.sha256((ID_j + SSK_j + T1).encode()).hexdigest(), 16) ^ int(UID_i, 16))[2:].zfill(64)
    beta_i = hashlib.sha256((UID_i + SSK_j + C_i + T1).encode()).hexdigest()

    data = {"alpha_i": alpha_i, "beta_i": beta_i, "T1": T1, "UID_i": UID_i, "C_i": C_i}  # Include UID_i and C_i
    try:
        response = requests.post(f"{Server_URL}/authenticate", json=data)
        response.raise_for_status()
        result = response.json()

        gamma_i = result.get("gamma_i")
        sigma_i = result.get("sigma_i")
        T2 = result.get("T2")
        VT_ij = result.get("VT_ij")
        Loc_j = result.get("Loc_j")

        # 3. Verification of Server's Response
        delta_T = 10  # Example
        T3 = str(time.time())
        if float(T3) - float(T2) > delta_T:
            print("Authentication failed: Timestamp expired")
            return

        hash_cuididjbeta = hashlib.sha256((C_i + UID_i + ID_j + beta_i).encode()).hexdigest()
        VT_ij_Loc_j = hex(int(gamma_i, 16) ^ int(hash_cuididjbeta, 16))[2:].zfill(64)

        sigma_i_prime = hashlib.sha256((VT_ij + C_i + str(float(T2) - float(T1))).encode()).hexdigest()

        if sigma_i_prime != sigma_i:
            print("Authentication failed: Invalid server response")
            return

        # 4. Session Key Agreement
        SK_ij = hashlib.sha256((UID_i + ID_j + C_i + Loc_j + VT_ij).encode()).hexdigest()
        print(f"Authentication successful. Session Key: {SK_ij}")

    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")

if __name__ == "__main__":
    register_user()
    SmartCard_i = load_user_data()
    if SmartCard_i:
        authenticate_with_server()
    else:
        print("Registration Failed")
