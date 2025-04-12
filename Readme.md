
# 🛡️ Privacy-Preserving Mutual Authentication and Key Agreement Protocol

**A secure and efficient multi-server authentication scheme** implemented in Python, based on the IEEE Access paper:

> **"Privacy-Preserving Mutual Authentication and Key Agreement Scheme for Multi-Server Healthcare System"**  
> _Limbasiya, Sahay, Sridharan – IEEE Access, 2020_

---

## 🔗 Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Phases Implemented](#phases-implemented)
- [Cryptographic Design](#cryptographic-design)
- [Project Structure](#project-structure)
- [Setup & Execution](#setup--execution)
- [Usage Examples](#usage-examples)
- [Security Features](#security-features)
- [Authors & Credits](#authors--credits)

---

## 🧠 Overview

This project simulates a lightweight authentication and session key agreement protocol for distributed healthcare systems where users can securely authenticate with multiple servers without re-registering.

The system uses only SHA-256 and XOR operations — making it ideal for resource-constrained IoT or healthcare environments.

---

## 🧱 System Components

| Role     | Description |
|----------|-------------|
| 🧑‍⚕️ **User (U<sub>i</sub>)** | Registers once with RC, authenticates with any registered server |
| 🏥 **Server (S<sub>j</sub>)** | Healthcare servers, each with unique credentials |
| 🛡️ **Registration Center (RC)** | Central trusted authority handling user/server registration and credential management |

---

## 🔄 Phases Implemented

### **1️⃣ Server Registration**

- The server sends `ID_j`, `P_j = h(ID_j || r_S || PW_j)`, and `Q_j = h(ID_j || PW_j) ⊕ P_j` to RC.
- The RC registers the server and returns a shared secret key `SSK_j = h(K_rc || P_j || SRT_j)`.
- RC stores `ID_j`, `SSK_j`, `Loc_j`, `Q_j`.

✅ Implemented in `server1.py` and `rc.py`  
🔗 Endpoint: `POST /register_server`

---

### **2️⃣ User Registration**

- The user sends `UID_i = h(r1 || ID_i || r2)` and `A_i = h(ID_i || PW_i)` to RC.
- RC generates a unique session key `USK_i`, and computes:
  - `C_i = h(K_rc || r3 || A_i) ⊕ USK_i ⊕ h(UID_i || A_i)`
  - `D_i = A_i ⊕ USK_i`
- RC returns `{C_i, D_i, List_sj}` to user.
- User builds smartcard with:
  - `W_i`, `X_i`, `Y_i`, `Z_i = h(r1 || ID_i || PW_i) ⊕ h(ID_i || PW_i || r2) ⊕ List_sj`, `E_i = h(UID_i || PW_i || USK_i)`

✅ Implemented in `user1.py` and `rc.py`  
🔗 Endpoint: `POST /register_user`

---

### **3️⃣ Authentication and Key Agreement**

- **Step 1**: User → Server:
  - Sends `α_i = UID_i ⊕ h(ID_j || SSK_j || T1)`
  - Sends `β_i = h(UID_i || SSK_j || C_i || T1)`
- **Step 2**: Server verifies `β_i`, responds with:
  - `γ_i = (VT_ij + Loc_j) ⊕ h(C_i || UID_i || ID_j || β_i)`
  - `σ_i = h(VT_ij || C_i || (T2 - T1))`
- **Step 3**: User verifies `σ_i`, and both parties compute:
  ```python
  SK_ij = h(UID_i || ID_j || C_i || Loc_j || VT_ij)
  ```

✅ Fully implemented in `user1.py` and `server1.py`  
🔗 Endpoint: `POST /authenticate`

---

### **4️⃣ Password / Smartcard Update**

- User authenticates using smartcard (`E_i`) and sends a request to update password.
- RC verifies UID and recalculates updated `C_i`, `D_i` using new `PW_i`.

✅ Implemented in `user1.py` and `rc.py`  
🔗 Endpoint: `POST /update_password`

---

### **5️⃣ Server Database Update**

- Server sends `ID_j` and timestamp `T` to RC to refresh or re-register.
- RC verifies timestamp freshness and updates the database accordingly.

✅ Implemented in `server1.py` and `rc.py`  
🔗 Endpoint: `POST /update_server_db`

---

## 🔐 Cryptographic Design

- Hash function: `h(x) = SHA-256(x)`
- All credentials derived from hash and XOR — no public key crypto required
- **Smartcard Encodings:**
  - `Z_i = h(r1 || ID_i || PW_i) ⊕ h(ID_i || PW_i || r2) ⊕ List_sj`
  - `E_i = h(UID_i || PW_i || USK_i)`
- **Session Key:**
  ```python
  SK_ij = h(UID_i || ID_j || C_i || Loc_j || VT_ij)
  ```

---

## 📁 Project Structure

```
project/
├── rc.py              # Registration Center (Flask app)
├── server1.py         # Hospital server (Flask app)
├── user1.py           # User script for registration & authentication
├── rc.db              # SQLite DB: RC stores users and servers
├── server.db          # SQLite DB: Local server storage
├── user_data.json     # Smartcard simulation (user-side file)
```

---

## ⚙️ Setup & Execution

### ✅ Install requirements
```bash
pip install flask requests
```

### ✅ Run Registration Center (RC)
```bash
python rc.py   # runs on http://localhost:5000
```

### ✅ Run Server
```bash
python server1.py  # runs on http://localhost:5001
```

### ✅ Run User
```bash
python user1.py
```

---

## 🧪 Usage Examples

### 🔐 Register + Authenticate
User will auto-register and authenticate using `/register_user` and `/authenticate`.

### 🔑 Update Password
In `user1.py`:
```python
update_password("new_secure_password123")
```

### 🏥 Server Database Refresh
In `server1.py` or with curl:
```bash
curl -X POST http://localhost:5001/update_server_db
```

---

## 🔒 Security Features

- ✔️ One-time registration
- ✔️ Forward secrecy via nonces and timestamps
- ✔️ List<sub>sj</sub> confidentiality using XOR
- ✔️ Replay protection via `T1`, `T2`
- ✔️ User anonymity (`UID_i` is always hashed and masked)

---

## 👨‍💻 Authors & Credits

This project was implemented as part of a research/learning exercise based on the paper:

📄 _"Privacy-Preserving Mutual Authentication and Key Agreement Scheme for Multi-Server Healthcare System"_  
IEEE Access 2020 – Limbasiya, Sahay, Sridharan  
🔗 [DOI: 10.1109/ACCESS.2020.3015354](https://ieeexplore.ieee.org/document/9153859)

---


