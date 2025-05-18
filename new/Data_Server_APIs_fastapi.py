# data_server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import logging

# === Logging ===
logging.basicConfig(
    filename='dataserver.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

def log(msg: str):
    print(msg)
    logging.info(msg)

# === Redis client ===
r = redis.Redis(host="localhost", port=6379, db=0)

# === FastAPI App ===
app = FastAPI()

# === CORS support ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可根據實際情況限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Request Models ===
class UploadRequest(BaseModel):
    file_name: str
    encrypted_data: str
    encrypted_aes_key: str

# === Utilities ===
def file_exists(fname: str) -> bool:
    return r.exists(f"filedata:{fname}")

def save_file(fname: str, data: str, aes_key: str):
    key = f"filedata:{fname}"
    r.hset(key, mapping={
        'encrypted_data': data,
        'encrypted_aes_key': aes_key
    })

def get_file(fname: str):
    key = f"filedata:{fname}"
    if not r.exists(key):
        return None
    rec = r.hgetall(key)
    return {k.decode(): v.decode() for k, v in rec.items()}

# === Endpoints ===

@app.post("/upload")
async def upload_file(payload: UploadRequest):
    if not payload.file_name or not payload.encrypted_data or not payload.encrypted_aes_key:
        raise HTTPException(status_code=400, detail="missing_fields")

    if file_exists(payload.file_name):
        raise HTTPException(status_code=409, detail="file_exists")

    save_file(payload.file_name, payload.encrypted_data, payload.encrypted_aes_key)
    log(f"[UPLOAD] Stored file '{payload.file_name}' in Redis")
    return {"status": "upload_success"}

@app.get("/download")
async def download_file(file_name: str):
    record = get_file(file_name)
    if not record:
        raise HTTPException(status_code=404, detail="file_not_found")

    log(f"[DOWNLOAD] Retrieved file '{file_name}' from Redis")
    return {
        "encrypted_data": record["encrypted_data"],
        "encrypted_aes_key": record["encrypted_aes_key"]
    }

import uvicorn

if __name__ == "__main__":
    log("Flushing Redis database for a clean start...")
    r.flushdb()
    log("Starting Data Server with FastAPI on port 4000")
    uvicorn.run(app, host="0.0.0.0", port=4000)
