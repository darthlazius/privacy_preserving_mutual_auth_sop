from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import hashlib, secrets, time, requests, json, os, logging
from datetime import datetime

# === CONFIGURATION ===
RC_URL = os.environ.get("RC_URL", "http://127.0.0.1:5000")      # Registration Center
SERVER_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:5001")  # Hospital Server
USER_DATA_FILE = "user_data.json"
PERFORMANCE_LOG_FILE = "performance_metrics.log"

# === PERFORMANCE LOGGING SETUP ===
perf_logger = logging.getLogger("performance")
perf_logger.setLevel(logging.INFO)
perf_handler = logging.FileHandler(PERFORMANCE_LOG_FILE)
perf_formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f')
perf_handler.setFormatter(perf_formatter)
perf_logger.addHandler(perf_handler)
perf_logger.propagate = False

app = FastAPI(title="User Middleware API", version="1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression for faster response times
app.add_middleware(GZipMiddleware, minimum_size=500)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache HTML in memory for faster loading
_HTML_CACHE = None
def get_cached_html():
    global _HTML_CACHE
    if _HTML_CACHE is None:
        try:
            with open("index.html", "r") as f:
                _HTML_CACHE = f.read()
        except FileNotFoundError:
            _HTML_CACHE = ""
    return _HTML_CACHE

# ====================== UTILITY FUNCTIONS ======================
def calculate_A_i(ID_i, PW_i):
    return hashlib.sha256((ID_i + PW_i).encode()).hexdigest()

def calculate_wi(r1, r2, A_i):
    r1r2_int = int((r1 + r2).encode('utf-8').hex(), 16) ^ int(A_i, 16)
    return hex(r1r2_int)[2:].zfill(64)

def calculate_B_i(r1, r2, PW_i):
    t1 = hashlib.sha256((r1 + PW_i).encode()).hexdigest()
    t2 = hashlib.sha256((r2 + PW_i).encode()).hexdigest()
    return hex(int(t1, 16) ^ int(t2, 16))[2:].zfill(64)

def compute_z_i(r1, r2, ID_i, PW_i, list_sj_str):
    h1 = hashlib.sha256((r1 + ID_i + PW_i).encode()).hexdigest()
    h2 = hashlib.sha256((ID_i + PW_i + r2).encode()).hexdigest()
    list_sj_int = int(list_sj_str.encode('utf-8').hex(), 16)
    return hex(int(h1, 16) ^ int(h2, 16) ^ list_sj_int)[2:].zfill(64)

def extract_list_sj_from_z(Z_i, r1, r2, ID_i, PW_i):
    h1 = hashlib.sha256((r1 + ID_i + PW_i).encode()).hexdigest()
    h2 = hashlib.sha256((ID_i + PW_i + r2).encode()).hexdigest()
    list_sj_int = int(Z_i, 16) ^ int(h1, 16) ^ int(h2, 16)
    try:
        s_bytes = bytes.fromhex(hex(list_sj_int)[2:].zfill(64))
        return s_bytes.decode("utf-8", errors="ignore").strip().split(";")
    except:
        return []

def extract_server_details(List_sj, target_server_id):
    for entry in List_sj:
        parts = entry.split(".")
        if len(parts) == 3:
            ID_j, SSK_j, Loc_j = parts
            if ID_j == target_server_id:
                return SSK_j, Loc_j
    return None, None

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return None

# ====================== REGISTRATION ======================
@app.post("/register_user")
async def register_user(req: Request):
    t_start = time.perf_counter()
    data = await req.json()
    ID_i = data.get("user_id")
    PW_i = data.get("password")

    if not ID_i or not PW_i:
        return JSONResponse({"error": "Missing user credentials"}, status_code=400)

    try:
        # Phase 1: Initial credential computation
        t1 = time.perf_counter()
        r1, r2 = secrets.token_hex(16), secrets.token_hex(16)
        UID_i = hashlib.sha256((r1 + ID_i + r2).encode()).hexdigest()
        A_i = calculate_A_i(ID_i, PW_i)
        B_i = calculate_B_i(r1, r2, PW_i)
        t_initial = (time.perf_counter() - t1) * 1000  # Convert to ms

        # Phase 2: RC communication
        t2 = time.perf_counter()
        rc_payload = {"UID_i": UID_i, "A_i": A_i}
        rc_response = requests.post(f"{RC_URL}/register_user", json=rc_payload)
        if rc_response.status_code != 201:
            return JSONResponse({"error": "RC registration failed"}, status_code=rc_response.status_code)
        rc_data = rc_response.json()
        t_rc_comm = (time.perf_counter() - t2) * 1000

        # Phase 3: Smartcard computation
        t3 = time.perf_counter()
        List_sj = rc_data.get("List_sj", [])
        list_sj_str = ";".join(List_sj)

        Z_i = compute_z_i(r1, r2, ID_i, PW_i, list_sj_str)
        W_i = calculate_wi(r1, r2, A_i)
        C_i, D_i = rc_data.get("C_i"), rc_data.get("D_i")

        r2_id = hashlib.sha256((r2 + ID_i).encode()).hexdigest()
        r1_pw = hashlib.sha256((r1 + PW_i).encode()).hexdigest()

        X_i = hex(int(r2_id, 16) ^ int(r1_pw, 16) ^ int(C_i, 16))[2:].zfill(64)
        Y_i = hex(int(B_i, 16) ^ int(D_i, 16))[2:].zfill(64)
        USK_i = hex(int(A_i, 16) ^ int(D_i, 16))[2:].zfill(64)
        E_i = hashlib.sha256((UID_i + PW_i + USK_i).encode()).hexdigest()

        SmartCard_i = {"W_i": W_i, "X_i": X_i, "Y_i": Y_i, "Z_i": Z_i, "E_i": E_i}
        save_user_data(SmartCard_i)
        t_smartcard = (time.perf_counter() - t3) * 1000

        t_total = (time.perf_counter() - t_start) * 1000

        # Log performance metrics
        perf_logger.info(f"REGISTRATION | user={ID_i} | initial_comp={t_initial:.3f}ms | rc_comm={t_rc_comm:.3f}ms | smartcard_comp={t_smartcard:.3f}ms | TOTAL={t_total:.3f}ms")

        return JSONResponse({
            "message": "User registered successfully",
            "UID_i": UID_i,
            "E_i": E_i,
            "SmartCard": SmartCard_i
        }, status_code=201)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ====================== AUTHENTICATION ======================
@app.post("/authenticate_user")
async def authenticate_user(req: Request):
    t_start = time.perf_counter()
    data = await req.json()
    ID_i = data.get("user_id")
    PW_i = data.get("password")

    # Phase 1: Smartcard loading and initial computations
    t1 = time.perf_counter()
    SmartCard_i = load_user_data()
    if not SmartCard_i:
        return JSONResponse({"error": "Smartcard not found. Please register first."}, status_code=404)

    W_i, X_i, Y_i, Z_i, E_i = (SmartCard_i[k] for k in ["W_i", "X_i", "Y_i", "Z_i", "E_i"])
    A_i = calculate_A_i(ID_i, PW_i)
    r1r2 = int(W_i, 16) ^ int(A_i, 16)
    # Fix: Need to decode UTF-8 to get original r1+r2 string, not convert to hex
    r1r2_hex = hex(r1r2)[2:]
    # Pad to even length for bytes.fromhex
    if len(r1r2_hex) % 2 == 1:
        r1r2_hex = '0' + r1r2_hex
    r1r2_bytes = bytes.fromhex(r1r2_hex)
    r1r2_str = r1r2_bytes.decode('utf-8', errors='ignore')
    r1, r2 = r1r2_str[:32], r1r2_str[32:]
    t_smartcard_load = (time.perf_counter() - t1) * 1000

    # Phase 2: Credential verification
    t2 = time.perf_counter()
    UID_i = hashlib.sha256((r1 + ID_i + r2).encode()).hexdigest()
    B_i = calculate_B_i(r1, r2, PW_i)
    D_i = hex(int(Y_i, 16) ^ int(B_i, 16))[2:].zfill(64)
    USK_i = hex(int(A_i, 16) ^ int(D_i, 16))[2:].zfill(64)
    E_i_computed = hashlib.sha256((UID_i + PW_i + USK_i).encode()).hexdigest()

    # Debug logging
    print(f"[DEBUG] user_id={ID_i}")
    print(f"[DEBUG] r1={r1[:16]}... r2={r2[:16]}...")
    print(f"[DEBUG] A_i={A_i[:16]}...")
    print(f"[DEBUG] E_i_stored={E_i[:16]}...")
    print(f"[DEBUG] E_i_computed={E_i_computed[:16]}...")
    print(f"[DEBUG] Match: {E_i_computed == E_i}")

    if E_i_computed != E_i:
        return JSONResponse({"error": "Invalid credentials. Please check your user ID and password."}, status_code=401)
    t_credential_verify = (time.perf_counter() - t2) * 1000

    # Phase 3: Server lookup
    t3 = time.perf_counter()
    List_sj = extract_list_sj_from_z(Z_i, r1, r2, ID_i, PW_i)
    rc_info = requests.get(SERVER_URL).json()
    ID_j = rc_info["creds"]["ID_j"]
    SSK_j, Loc_j = extract_server_details(List_sj, ID_j)
    if not SSK_j:
        return JSONResponse({"error": f"Server {ID_j} not found in List_sj"}, status_code=404)
    t_server_lookup = (time.perf_counter() - t3) * 1000

    # Phase 4: Authentication message preparation
    t4 = time.perf_counter()
    T1 = str(int(time.time()))
    h1 = hashlib.sha256((ID_j + SSK_j + T1).encode()).hexdigest()
    alpha_i = hex(int(UID_i, 16) ^ int(h1, 16))[2:].zfill(64)
    r2_id = hashlib.sha256((r2 + ID_i).encode()).hexdigest()
    r1_pw = hashlib.sha256((r1 + PW_i).encode()).hexdigest()
    C_i = hex(int(X_i, 16) ^ int(r2_id, 16) ^ int(r1_pw, 16))[2:].zfill(64)
    beta_i = hashlib.sha256((UID_i + SSK_j + C_i + T1).encode()).hexdigest()
    t_msg_prep = (time.perf_counter() - t4) * 1000

    # Phase 5: Server communication
    t5 = time.perf_counter()
    payload = {"alpha_i": alpha_i, "beta_i": beta_i, "T1": T1, "C_i": C_i, "UID_i": UID_i, "ID_j": ID_j}
    res = requests.post(f"{SERVER_URL}/authenticate", json=payload)
    if res.status_code != 200:
        return JSONResponse({"error": res.text}, status_code=res.status_code)
    t_server_comm = (time.perf_counter() - t5) * 1000

    # Phase 6: Response verification and session key computation
    t6 = time.perf_counter()
    data = res.json()
    gamma_i, sigma_i, T2 = data["gamma_i"], data["sigma_i"], int(data["T2"])
    T3 = int(time.time())
    if T3 - T2 > 60:
        return JSONResponse({"error": "Server response too old"}, status_code=408)

    h_comb = hashlib.sha256((C_i + UID_i + ID_j + beta_i).encode()).hexdigest()
    vt_loc = int(gamma_i, 16) ^ int(h_comb, 16)
    SK_ij = hashlib.sha256((UID_i + ID_j + C_i + Loc_j + hex(vt_loc)[2:]).encode()).hexdigest()
    t_verify_sk = (time.perf_counter() - t6) * 1000

    t_total = (time.perf_counter() - t_start) * 1000

    # Log detailed performance metrics
    perf_logger.info(f"AUTHENTICATION | user={ID_i} | smartcard_load={t_smartcard_load:.3f}ms | credential_verify={t_credential_verify:.3f}ms | server_lookup={t_server_lookup:.3f}ms | msg_prep={t_msg_prep:.3f}ms | server_comm={t_server_comm:.3f}ms | verify_sk={t_verify_sk:.3f}ms | TOTAL={t_total:.3f}ms")

    return JSONResponse({
        "message": "Mutual authentication successful",
        "session_key": SK_ij,
        "timestamp": T2
    }, status_code=200)


@app.get("/", response_class=HTMLResponse)
async def home():
    html = get_cached_html()
    if html:
        return html
    return {"message": "User Middleware API is running 🚀"}

@app.get("/health")
def health():
    return {"message": "User Middleware API is running 🚀", "status": "healthy"}
