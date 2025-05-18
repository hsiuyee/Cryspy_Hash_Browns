from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import logging
import base64
import smtplib
from email.mime.text import MIMEText
from Crypto.PublicKey import RSA

# === Setup logging ===
logging.basicConfig(
    filename='kms.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

def log(msg):
    print(msg)
    logging.info(msg)

# === Flask app ===
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# In-memory stores
pending_registrations = {}  # email -> { password_hash, otp }
users = {}                  # email -> { password_hash }
sessions = {}               # sid -> email
files = {}                 # file_name -> { public_key, private_key, owner }
access_table = {}          # file_name -> list of friend_emails

# === SMTP Settings ===
SMTP_SERVER = 'smtp.cs.nctu.edu.tw'
SMTP_PORT = 25
SENDER_EMAIL = 'liaohi@cs.nycu.edu.tw'
SENDER_PASS = 'A131710916a@'

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

# === Utilities ===
def gen_otp():
    return str(random.randint(100000, 999999))

def gen_sid():
    sid = str(random.randint(10000000, 99999999))
    log(f"[SESSION] Generated sid: {sid}")
    return sid

# === Endpoints ===

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data["email"]
    password_hash = data["password_hash"]
    if email in users or email in pending_registrations:
        return jsonify({"error": "user_exists"})
    otp = gen_otp()
    pending_registrations[email] = {"password_hash": password_hash, "otp": otp}
    log(f"[EMAIL] Sending verification OTP to {email}: {otp}")
    send_otp_to_email(email, otp)
    return jsonify({"status": "registration_pending"})

@app.route("/verify_email", methods=["POST"])
def verify_email():
    data = request.get_json()
    email = data["email"]
    otp = data["otp"]
    if email not in pending_registrations:
        return jsonify({"error": "no_pending_registration"})
    if pending_registrations[email]["otp"] != otp:
        del pending_registrations[email]  # Remove on failed attempt
        return jsonify({"error": "otp_invalid"})
    password_hash = pending_registrations[email]["password_hash"]
    users[email] = {"password_hash": password_hash}
    del pending_registrations[email]
    return jsonify({"status": "email_verified"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data["email"]
    password_hash = data["password_hash"]
    if email not in users or users[email]["password_hash"] != password_hash:
        return jsonify({"error": "login_error"})
    otp = gen_otp()
    users[email]["otp"] = otp
    log(f"[MOCK EMAIL] Login OTP to {email}: {otp}")
    return jsonify({"status": "login_otp_sent"})

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data["email"]
    otp = data["otp"]
    if email not in users or users[email].get("otp") != otp:
        return jsonify({"error": "otp_failed"})
    sid = gen_sid()
    sessions[sid] = email
    return jsonify({"status": "login_success", "sid": sid})

@app.route("/get_public_key", methods=["POST"])
def get_public_key():
    data = request.get_json()
    file_name = data["file_name"]
    sid = request.headers.get("sid")

    # DEBUG
    log(f"[GET_PUBLIC_KEY] Incoming sid: {sid}")
    log(f"[GET_PUBLIC_KEY] Sessions store: {sessions}")

    if sid not in sessions:
        return jsonify({"error": "invalid_session"})
    owner = sessions[sid]
    if file_name in files:
        return jsonify({"error": "file_exists"})
    rsa_key = RSA.generate(2048)
    pub_key = base64.b64encode(rsa_key.publickey().export_key()).decode()
    priv_key = base64.b64encode(rsa_key.export_key()).decode()
    files[file_name] = {"public_key": pub_key, "private_key": priv_key, "owner": owner}
    access_table[file_name] = [owner]
    return jsonify({"kms_public_key": pub_key})

@app.route("/get_private_key", methods=["POST"])
def get_private_key():
    sid = request.headers.get("sid")
    data = request.get_json()
    file_name = data["file_name"]
    if sid not in sessions:
        return jsonify({"error": "invalid_session"})
    user = sessions[sid]
    if file_name not in access_table or user not in access_table[file_name]:
        return jsonify({"error": "access_denied"})
    return jsonify({"kms_private_key": files[file_name]["private_key"]})

@app.route("/grant_access", methods=["POST"])
def grant_access():
    sid = request.headers.get("sid")
    data = request.get_json()
    file_name = data["file_name"]
    friend_email = data["friend_email"]
    if sid not in sessions:
        return jsonify({"error": "invalid_session"})
    owner = sessions[sid]
    if file_name not in files or files[file_name]["owner"] != owner:
        return jsonify({"error": "permission_denied"})
    if friend_email not in access_table[file_name]:
        access_table[file_name].append(friend_email)
    # Log the updated access table for this file
    log(f"[GRANT_ACCESS] Updated access_table for '{file_name}': {access_table[file_name]}")
    return jsonify({"status": "grant_success"})

if __name__ == "__main__":
    log("Starting secure KMS server on port 3000")
    app.run(port=3000)