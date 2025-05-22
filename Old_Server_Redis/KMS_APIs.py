# KmsServerRedis.py
# KMS Server implementation using Redis instead of in-memory dicts

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import logging
import base64
import smtplib
from email.mime.text import MIMEText
from Crypto.PublicKey import RSA
import redis

# === Setup logging ===
logging.basicConfig(
    filename='kms.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

def log(msg):
    print(msg)
    logging.info(msg)

# === Redis client ===
r = redis.Redis(host='localhost', port=6379, db=0)

# === Flask app ===
app = Flask(__name__)
CORS(app)

# === SMTP Settings ===
SMTP_SERVER = 'smtp.cs.nctu.edu.tw'
SMTP_PORT = 25
SENDER_EMAIL = 'liaohi@cs.nycu.edu.tw'
SENDER_PASS = 'A131710916a@'

# === Utilities ===
def send_otp_to_email(receiver_email, otp_code):
    subject = 'Your 2FA Code'
    body = f'Your verification code is: {otp_code}'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())

def gen_otp():
    return str(random.randint(100000, 999999))

def gen_sid():
    sid = str(random.randint(10000000, 99999999))
    log(f"[SESSION] Generated sid: {sid}")
    return sid

# === Redis-backed operations ===

# Pending registrations: hash pending:{email} fields password_hash, otp (TTL 600s)
def save_pending(email, pw, otp):
    key = f"pending:{email}"
    r.hmset(key, {"password_hash": pw, "otp": otp})
    r.expire(key, 600)

def get_pending(email):
    key = f"pending:{email}"
    if not r.exists(key): return None
    return r.hgetall(key)

def clear_pending(email):
    r.delete(f"pending:{email}")

# Users: hash user:{email} fields password_hash, otp? (otp TTL 300s)
def save_user(email, pw):
    key = f"user:{email}"
    r.hset(key, "password_hash", pw)

def get_user(email):
    key = f"user:{email}"
    if not r.exists(key): return None
    return r.hgetall(key)

# Sessions: hash sessions sid -> email (TTL 1800s)
def save_session(sid, email):
    r.hset("sessions", sid, email)
    r.expire("sessions", 1800)

def get_session(sid):
    return r.hget("sessions", sid)

# Files: hash file:{file_name} fields public_key, private_key, owner
# Access: set access:{file_name}
def save_file_keys(fname, pub, priv, owner):
    key = f"file:{fname}"
    r.hmset(key, {"public_key": pub, "private_key": priv, "owner": owner})

def file_exists(fname):
    return r.exists(f"file:{fname}")

def save_access(fname, email):
    r.sadd(f"access:{fname}", email)

def has_access(fname, email):
    return r.sismember(f"access:{fname}", email)

# === Endpoints ===

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data["email"]
    pw = data["password_hash"]
    if get_user(email) or r.exists(f"pending:{email}"):
        return jsonify({"error": "user_exists"})
    otp = gen_otp()
    save_pending(email, pw, otp)
    log(f"[EMAIL] Sending verification OTP to {email}: {otp}")
    send_otp_to_email(email, otp)
    return jsonify({"status": "registration_pending"})

@app.route("/verify_email", methods=["POST"])
def verify_email():
    data = request.get_json()
    email, otp = data["email"], data["otp"]
    pending = get_pending(email)
    if not pending:
        return jsonify({"error": "no_pending_registration"})
    if pending[b"otp"].decode() != otp:
        clear_pending(email)
        return jsonify({"error": "otp_invalid"})
    save_user(email, pending[b"password_hash"].decode())
    clear_pending(email)
    return jsonify({"status": "email_verified"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data["email"]
    password_hash = data["password_hash"]
    user = get_user(email)
    if not user or user[b"password_hash"].decode() != password_hash:
        return jsonify({"error": "login_error"})
    otp = gen_otp()
    # reuse pending for login OTP
    save_pending(email, password_hash, otp)
    log(f"[EMAIL] Login OTP to {email}: {otp}")
    send_otp_to_email(email, otp)
    return jsonify({"status": "login_otp_sent"})

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data["email"]
    otp = data["otp"]
    pending = get_pending(email)
    if not pending or pending[b"otp"].decode() != otp:
        return jsonify({"error": "otp_failed"})
    sid = gen_sid()
    save_session(sid, email)
    clear_pending(email)
    return jsonify({"status": "login_success", "sid": sid})

@app.route("/get_public_key", methods=["POST"])
def get_public_key():
    data = request.get_json()
    file_name = data["file_name"]
    sid = request.headers.get("sid")
    log(f"[GET_PUBLIC_KEY] sid: {sid}")

    if not get_session(sid): 
        return jsonify({"error": "invalid_session"})
    if file_exists(file_name): 
        return jsonify({"error": "file_exists"})
    
    rsa_key = RSA.generate(2048)
    pub = base64.b64encode(rsa_key.publickey().export_key()).decode()
    priv = base64.b64encode(rsa_key.export_key()).decode()
    save_file_keys(file_name, pub, priv, get_session(sid).decode())
    save_access(file_name, get_session(sid).decode())
    return jsonify({"kms_public_key": pub})

@app.route("/get_private_key", methods=["POST"])
def get_private_key():
    data = request.get_json()
    file_name = data["file_name"]
    sid = request.headers.get("sid")
    if not get_session(sid):
        return jsonify({"error": "invalid_session"})
    user = get_session(sid).decode()
    if not has_access(file_name, user):
        return jsonify({"error": "access_denied"})
    key = r.hget(f"file:{file_name}", "private_key").decode()
    return jsonify({"kms_private_key": key})

@app.route("/grant_access", methods=["POST"])
def grant_access():
    data = request.get_json()
    file_name = data["file_name"]
    friend = data["friend_email"]
    sid = request.headers.get("sid")
    if not get_session(sid):
        return jsonify({"error": "invalid_session"})
    owner = get_session(sid).decode()
    rec = r.hgetall(f"file:{file_name}")
    if not rec or rec[b"owner"].decode() != owner:
        return jsonify({"error": "permission_denied"})
    save_access(file_name, friend)
    log(f"[GRANT_ACCESS] {friend} granted on {file_name}")
    return jsonify({"status": "grant_success"})

if __name__ == "__main__":
    # Flush Redis DB on startup to clear previous state
    log("Flushing Redis database for a clean start...")
    r.flushdb()
    log("Starting KMS Server with Redis on port 3000")
    app.run(port=3000)
