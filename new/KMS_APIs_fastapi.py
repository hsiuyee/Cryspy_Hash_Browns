from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import logging
import base64
import smtplib
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
from fastapi.responses import JSONResponse
=======
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py
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
SMTP_SERVER = 'smtp.cs.nctu.edu.tw'
SMTP_PORT = 25
SENDER_EMAIL = 'liaohi@cs.nycu.edu.tw'
SENDER_PASS = 'A131710916a@'

# === Models ===
class RegisterRequest(BaseModel):
    email: str
    password_hash: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class LoginRequest(BaseModel):
    email: str
    password_hash: str

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
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
        log(f"[REGISTER] User {req.email} already exists (status_code: 400)")
        return JSONResponse(content={"code": 400, "message": "user_exists"})
=======
        raise HTTPException(status_code=400, detail="user_exists")
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py
    otp = gen_otp()
    save_pending(req.email, req.password_hash, otp)
    log(f"[EMAIL] Sending verification OTP to {req.email}: {otp}")
    send_otp_to_email(req.email, otp)
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
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
=======
    return {"status": "registration_pending"}

@app.post("/verify_email")
async def verify_email(req: OTPVerifyRequest):
    pending = get_pending(req.email)
    if not pending:
        raise HTTPException(status_code=400, detail="no_pending_registration")
    if pending[b"otp"].decode() != req.otp:
        clear_pending(req.email)
        raise HTTPException(status_code=400, detail="otp_invalid")
    save_user(req.email, pending[b"password_hash"].decode())
    clear_pending(req.email)
    return {"status": "email_verified"}
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py

@app.post("/login")
async def login(req: LoginRequest):
    user = get_user(req.email)
    if not user or user[b"password_hash"].decode() != req.password_hash:
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
        log(f"[LOGIN] Login failed for {req.email} (status_code: 401)")
        return JSONResponse(content={"code": 401, "message": "login_failed"})
=======
        raise HTTPException(status_code=401, detail="login_error")
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py
    otp = gen_otp()
    save_pending(req.email, req.password_hash, otp)
    log(f"[EMAIL] Login OTP to {req.email}: {otp}")
    send_otp_to_email(req.email, otp)
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
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
=======
    return {"status": "login_otp_sent"}

@app.post("/verify_otp")
async def verify_otp(req: OTPVerifyRequest):
    pending = get_pending(req.email)
    if not pending or pending[b"otp"].decode() != req.otp:
        raise HTTPException(status_code=401, detail="otp_failed")
    sid = gen_sid()
    save_session(sid, req.email)
    clear_pending(req.email)
    return {"status": "login_success", "sid": sid}
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py

@app.post("/get_public_key")
async def get_public_key(req: FileNameRequest, sid: Optional[str] = Header(None)):
    if not get_session(sid):
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
        log(f"[GET_PUBLIC_KEY] Invalid session for {sid} (status_code: 403)")
        return JSONResponse(content={"code": 403, "message": "invalid_session"})
    if file_exists(req.file_name):
        log(f"[GET_PUBLIC_KEY] File {req.file_name} already exists (status_code: 400)")
        return JSONResponse(content={"code": 400, "message": "file_exists"})
=======
        raise HTTPException(status_code=403, detail="invalid_session")
    if file_exists(req.file_name):
        raise HTTPException(status_code=400, detail="file_exists")
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py
    rsa_key = RSA.generate(2048)
    pub = base64.b64encode(rsa_key.publickey().export_key()).decode()
    priv = base64.b64encode(rsa_key.export_key()).decode()
    user = get_session(sid).decode()
    save_file_keys(req.file_name, pub, priv, user)
    save_access(req.file_name, user)
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
    log(f"[GET_PUBLIC_KEY] Public key saved for {req.file_name} (status_code: 200)")
    return JSONResponse(content={"code": 200, "message": "public_key_saved", "kms_public_key": pub})
=======
    return {"kms_public_key": pub}
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py

@app.post("/get_private_key")
async def get_private_key(req: FileNameRequest, sid: Optional[str] = Header(None)):
    if not get_session(sid):
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
        log(f"[GET_PRIVATE_KEY] Invalid session for {sid} (status_code: 403)")
        return JSONResponse(content={"code": 403, "message": "invalid_session"})
    user = get_session(sid).decode()
    if not has_access(req.file_name, user):
        log(f"[GET_PRIVATE_KEY] Access denied for {user} on {req.file_name} (status_code: 400)")
        return JSONResponse(content={"code": 400, "message": "access_denied"})
    key = r.hget(f"file:{req.file_name}", "private_key").decode()
    log(f"[GET_PRIVATE_KEY] Private key retrieved for {req.file_name} (status_code: 200)")
    return JSONResponse(content={"code": 200, "message": "private_key_retrieved", "kms_private_key": key})
=======
        raise HTTPException(status_code=403, detail="invalid_session")
    user = get_session(sid).decode()
    if not has_access(req.file_name, user):
        raise HTTPException(status_code=403, detail="access_denied")
    key = r.hget(f"file:{req.file_name}", "private_key").decode()
    return {"kms_private_key": key}
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py

@app.post("/grant_access")
async def grant_access(req: GrantAccessRequest, sid: Optional[str] = Header(None)):
    if not get_session(sid):
<<<<<<< HEAD:Redis_Server/KMS_APIs_fastapi.py
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
=======
        raise HTTPException(status_code=403, detail="invalid_session")
    owner = get_session(sid).decode()
    rec = r.hgetall(f"file:{req.file_name}")
    if not rec or rec[b"owner"].decode() != owner:
        raise HTTPException(status_code=403, detail="permission_denied")
    save_access(req.file_name, req.friend_email)
    log(f"[GRANT_ACCESS] {req.friend_email} granted on {req.file_name}")
    return {"status": "grant_success"}
>>>>>>> refs/remotes/origin/main:Server_Redis/KMS_APIs_fastapi.py

# === Startup ===
import uvicorn

if __name__ == "__main__":
    log("Flushing Redis database for a clean start...")
    r.flushdb()
    log("Starting KMS Server with FastAPI on port 3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)
