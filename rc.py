from flask import Flask, request, jsonify
import hashlib
import secrets
import time
import json
import sqlite3


app = Flask(__name__)

conn = sqlite3.connect('rc.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS servers(
            ID_j TEXT PRIMARY KEY,
            SSK_j TEXT,
            Loc_j TEXT,
            Q_j TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users(
            UID_i TEXT PRIMARY KEY,
            C_i TEXT)''')
conn.commit()
conn.close()

r3 = secrets.token_hex(16)  # Random number
K_rc = secrets.token_hex(32)  # RC's secret key

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

    conn = sqlite3.connect('rc.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT ID_j FROM servers WHERE ID_j = ?", (ID_j,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Server ID already exists"}), 409

    SRT_j = str(time.time())
    SSK_j = hashlib.sha256((K_rc + P_j + SRT_j).encode()).hexdigest()
    print(f"SSK_j: {SSK_j}")
    
    cursor.execute("INSERT INTO servers (ID_j, SSK_j, Loc_j, Q_j) VALUES (?, ?, ?, ?)",
    (ID_j, SSK_j, Loc_j, Q_j))
    conn.commit()
    conn.close()

    print(f"Server registered: {ID_j}")
    return jsonify({"SSK_j": SSK_j}), 201

@app.route('/register_user', methods=['POST'])
@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.get_json()
    UID_i = data.get('UID_i')
    A_i = data.get('A_i')

    if not UID_i or not A_i:
        return jsonify({"error": "Missing user parameters"}), 400

    try:
        conn = sqlite3.connect('rc.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT UID_i FROM users WHERE UID_i = ?", (UID_i,))
        if cursor.fetchone():
            return jsonify({"error": "User ID already exists"}), 409

        # Calculate USK_i
        USK_i = hashlib.sha256((K_rc + UID_i + r3).encode()).hexdigest()

        # Calculate C_i
        C_i = hex(int(hashlib.sha256((K_rc + r3 + A_i).encode()).hexdigest(), 16) ^ 
                  int(USK_i, 16) ^ 
                  int(hashlib.sha256((UID_i + A_i).encode()).hexdigest(), 16))[2:].zfill(64)

        # Calculate D_i
        D_i = hex(int(A_i, 16) ^ int(USK_i, 16))[2:].zfill(64)

        # Store in database
        cursor.execute("INSERT INTO users (UID_i, C_i) VALUES (?, ?)", (UID_i, C_i))
        conn.commit()

        # Get List_sj
        cursor.execute("SELECT ID_j, SSK_j, Loc_j FROM servers")
        rows = cursor.fetchall()
        List_sj = [f"{row[0]}.{row[1]}.{row[2]}" for row in rows]
        print(f"Fetched List_sj from DB: {List_sj}")

        SC_i = {"C_i": C_i, "D_i": D_i, "List_sj": List_sj}
        return jsonify(SC_i), 201

    except ValueError as ve:
        return jsonify({"error": f"Invalid A_i format: {ve}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()



@app.route('/update_server_db', methods=['POST'])
def rc_server_db_update():
    data = request.get_json()
    ID_j = data.get("ID_j")
    T = int(data.get("T", 0))

    if not ID_j or not T:
        return jsonify({"error": "Missing ID_j or timestamp"}), 400

    if abs(int(time.time()) - T) > 60:
        return jsonify({"error": "Timestamp too old. Possible replay attack."}), 403

    conn = sqlite3.connect('rc.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM servers WHERE ID_j = ?", (ID_j,))
    server = cursor.fetchone()

    if not server:
        conn.close()
        return jsonify({"error": "Server not found"}), 404

    # Optional: add new column "last_updated" and update it here
    # cursor.execute("UPDATE servers SET last_updated = ? WHERE ID_j = ?", (T, ID_j))

    conn.commit()
    conn.close()

    return jsonify({"message": f"Server {ID_j} verified and updated."}), 200



if __name__ == '__main__':
    app.run(port=5000, debug=True)