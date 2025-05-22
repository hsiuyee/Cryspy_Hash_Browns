# KMS_APIs_fastapi.py
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import logging
import base64
import smtplib
from fastapi.responses import JSONResponse
from email.mime.text import MIMEText
from Crypto.PublicKey import RSA
from dotenv import load_dotenv
import os
import redis
import bcrypt

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
load_dotenv()
r = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=0)

# === FastAPI app ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === SMTP Settings ===
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASS = os.getenv('SENDER_PASS')

# === Models ===
class RegisterRequest(BaseModel):
    email: str
    password: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class LoginRequest(BaseModel):
    email: str
    password: str

class FileNameRequest(BaseModel):
    file_name: str

class GrantAccessRequest(BaseModel):
    file_name: str
    friend_email: str

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
def save_pending(email, pw, otp):
    key = f"pending:{email}"
    r.hmset(key, {"password_hash": pw, "otp": otp})
    r.expire(key, 600)

def get_pending(email):
    key = f"pending:{email}"
    if not r.exists(key): return None
    return r.hgetall(key)

def get_user_password_hash(email):
    key = f"user:{email}"
    if not r.exists(key): return None
    return r.hget(key, "password_hash").decode()

def clear_pending(email):
    r.delete(f"pending:{email}")

def save_user(email, pw):
    key = f"user:{email}"
    r.hset(key, "password_hash", pw)

def get_user(email):
    key = f"user:{email}"
    if not r.exists(key): return None
    return r.hgetall(key)

def save_session(sid, email):
    r.hset("sessions", sid, email)
    r.expire("sessions", 1800)

def get_session(sid):
    return r.hget("sessions", sid)

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
@app.post("/register")
async def register(req: RegisterRequest):
    if get_user(req.email) or r.exists(f"pending:{req.email}"):
        log(f"[REGISTER] User {req.email} already exists (status_code: 400)")
        return JSONResponse(content={"code": 400, "message": "user_exists"})
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    otp = gen_otp()
    save_pending(req.email, password_hash, otp)
    log(f"[EMAIL] Sending verification OTP to {req.email}: {otp}")
    send_otp_to_email(req.email, otp)
    log(f"[REGISTER] OTP sent to {req.email}: {otp}")
    return JSONResponse(content={"code": 200, "message": "registration_pending"})

@app.post("/verify_register")
async def verify_register(req: OTPVerifyRequest):
    pending = get_pending(req.email)
    if not pending: # should not happen
        return JSONResponse(content={"code": 400, "message": "no_pending_registration"})
    if pending[b"otp"].decode() != req.otp:
        clear_pending(req.email)
        log(f"[EMAIL] OTP invalid for {req.email} (status_code: 401) - clear pending")
        return JSONResponse(content={"code": 401, "message": "otp_failed"})
    save_user(req.email, pending[b"password_hash"].decode())
    clear_pending(req.email)
    log(f"[REGISTER] User {req.email} verified (status_code: 200)")
    return JSONResponse(content={"code": 200, "message": "registration_success"})

@app.post("/login")
async def login(req: LoginRequest):
    stored_hash = get_user_password_hash(req.email)
    if not stored_hash or not bcrypt.checkpw(req.password.encode(), stored_hash.encode()):
        log(f"[LOGIN] Login failed for {req.email} (status_code: 401)")
        return JSONResponse(content={"code": 401, "message": "login_failed"})
    otp = gen_otp()
    save_pending(req.email, stored_hash, otp)
    log(f"[EMAIL] Login OTP to {req.email}: {otp}")
    send_otp_to_email(req.email, otp)
    log(f"[LOGIN] OTP sent to {req.email}: {otp}")
    return JSONResponse(content={"code": 200, "message": "login_otp_sent"})

@app.post("/verify_login")
async def verify_login(req: OTPVerifyRequest):
    pending = get_pending(req.email)
    if not pending or pending[b"otp"].decode() != req.otp:
        log(f"[LOGIN] OTP failed for {req.email} (status_code: 401)")
        return JSONResponse(content={"code": 401, "message": "otp_failed"})
    sid = gen_sid()
    save_session(sid, req.email)
    clear_pending(req.email)
    log(f"[LOGIN] Login success for {req.email} (status_code: 200)")
    return JSONResponse(content={"code": 200, "message": "login_success", "sid": sid})

@app.post("/get_public_key")
async def get_public_key(req: FileNameRequest, sid: Optional[str] = Header(None)):
    if not get_session(sid):
        log(f"[GET_PUBLIC_KEY] Invalid session for {sid} (status_code: 403)")
        return JSONResponse(content={"code": 403, "message": "invalid_session"})
    if file_exists(req.file_name):
        log(f"[GET_PUBLIC_KEY] File {req.file_name} already exists (status_code: 400)")
        return JSONResponse(content={"code": 400, "message": "file_exists"})
    rsa_key = RSA.generate(2048)
    pub = base64.b64encode(rsa_key.publickey().export_key()).decode()
    priv = base64.b64encode(rsa_key.export_key()).decode()
    user = get_session(sid).decode()
    save_file_keys(req.file_name, pub, priv, user)
    save_access(req.file_name, user)
    log(f"[GET_PUBLIC_KEY] Public key saved for {req.file_name} (status_code: 200)")
    return JSONResponse(content={"code": 200, "message": "public_key_saved", "kms_public_key": pub})

@app.post("/get_private_key")
async def get_private_key(req: FileNameRequest, sid: Optional[str] = Header(None)):
    if not get_session(sid):
        log(f"[GET_PRIVATE_KEY] Invalid session for {sid} (status_code: 403)")
        return JSONResponse(content={"code": 403, "message": "invalid_session"})
    user = get_session(sid).decode()
    if not has_access(req.file_name, user):
        log(f"[GET_PRIVATE_KEY] Access denied for {user} on {req.file_name} (status_code: 400)")
        return JSONResponse(content={"code": 400, "message": "access_denied"})
    key = r.hget(f"file:{req.file_name}", "private_key").decode()
    log(f"[GET_PRIVATE_KEY] Private key retrieved for {req.file_name} (status_code: 200)")
    return JSONResponse(content={"code": 200, "message": "private_key_retrieved", "kms_private_key": key})

@app.post("/grant_access")
async def grant_access(req: GrantAccessRequest, sid: Optional[str] = Header(None)):
    if not get_session(sid):
        log(f"[GRANT_ACCESS] Invalid session for {sid} (status_code: 403)")
        return JSONResponse(content={"code": 403, "message": "invalid_session"})
    owner = get_session(sid).decode()
    rec = r.hgetall(f"file:{req.file_name}")
    if not rec or rec[b"owner"].decode() != owner:
        log(f"[GRANT_ACCESS] Permission denied for {owner} on {req.file_name} (status_code: 400)")
        return JSONResponse(content={"code": 400, "message": "permission_denied"})
    save_access(req.file_name, req.friend_email)
    log(f"[GRANT_ACCESS] {req.friend_email} granted on {req.file_name} (status_code: 200)")
    return JSONResponse(content={"code": 200, "message": "grant_success"})

# === Startup ===
import uvicorn

if __name__ == "__main__":
    log("Flushing Redis database for a clean start...")
    r.flushdb()
    log("Starting KMS Server with FastAPI on port 3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)
