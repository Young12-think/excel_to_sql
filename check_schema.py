"""Cek skema tabel mol & gula di database timbangan."""
import pymysql, json, sys

# Coba pakai config.json, fallback ke localhost
try:
    cfg = json.load(open("dist/config.json"))
    host = cfg.get("db_host", "127.0.0.1")
except:
    host = "127.0.0.1"

# Coba beberapa credential
creds = [
    ("wb_rmi", "12345678"),
    ("root", ""),
    ("root", "12345678"),
]

conn = None
for user, pw in creds:
    try:
        conn = pymysql.connect(host=host, user=user, password=pw, database="timbangan")
        print(f"Connected as {user}@{host}")
        break
    except Exception as e:
        print(f"  Failed {user}: {e}")

if not conn:
    print("CANNOT CONNECT")
    sys.exit(1)

cur = conn.cursor()
tables = [
    "mol_penerimaan", "mol_delivery", "mol_stok_tangki",
    "gula_penerimaan", "gula_delivery", "gula_reject_log", "gula_stok"
]

for t in tables:
    try:
        cur.execute(f"SHOW COLUMNS FROM {t}")
        rows = cur.fetchall()
        print(f"\n=== {t} ===")
        for r in rows:
            print(f"  {r[0]:30s} {str(r[1]):30s} Null={r[2]} Key={r[3]} Default={r[4]}")
    except Exception as e:
        print(f"\n=== {t} === ERROR: {e}")

conn.close()
