# Data_Server_APIs_fastapi.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
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
load_dotenv()
r = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=0)

# === FastAPI App ===
app = FastAPI(
    title="Data Server",
    description="Encrypted file storage with AES data, key, and IV",
    version="1.0.0"
)

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
    encrypted_aes_initial_vector: str

# === Utilities ===

def file_exists(fname: str) -> bool:
    return r.exists(f"filedata:{fname}") == 1


def save_file(fname: str, data: str, aes_key: str, iv: str):
    key = f"filedata:{fname}"
    r.hset(key, mapping={
        'encrypted_data': data,
        'encrypted_aes_key': aes_key,
        'encrypted_aes_iv': iv
    })


def get_file(fname: str):
    key = f"filedata:{fname}"
    if not r.exists(key):
        return None
    rec = r.hgetall(key)
    return {k.decode(): v.decode() for k, v in rec.items()}

# === Endpoints ===

@app.post("/upload")
async def upload(payload: UploadRequest):
    # Validate all fields
    if not payload.file_name or not payload.encrypted_data \
       or not payload.encrypted_aes_key or not payload.encrypted_aes_initial_vector:
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": "missing_fields"}
        )
    if file_exists(payload.file_name):
        return JSONResponse(
            status_code=409,
            content={"code": 409, "message": "file_exists"}
        )
    save_file(
        payload.file_name,
        payload.encrypted_data,
        payload.encrypted_aes_key,
        payload.encrypted_aes_initial_vector
    )
    log(f"[UPLOAD] Stored file '{payload.file_name}' in Redis with IV")
    return JSONResponse(
        status_code=200,
        content={"code": 200, "message": "upload_success"}
    )

@app.get("/download")
async def download(file_name: str):
    record = get_file(file_name)
    if not record:
        return JSONResponse(
            status_code=404,
            content={"code": 404, "message": "file_not_found"}
        )
    log(f"[DOWNLOAD] Retrieved file '{file_name}' from Redis")
    return JSONResponse(
        status_code=200,
        content={
            "code": 200,
            "encrypted_data": record["encrypted_data"],
            "encrypted_aes_key": record["encrypted_aes_key"],
            "encrypted_aes_initial_vector": record["encrypted_aes_iv"]
        }
    )

@app.get("/list_files")
async def list_files():
    keys = r.keys("filedata:*")
    files = [k.decode().split("filedata:")[1] for k in keys]
    log(f"[LIST_FILES] Returning {len(files)} files")
    return JSONResponse(
        status_code=200,
        content={"code": 200, "files": files, "message": "list_files_success"}
    )

import uvicorn

if __name__ == "__main__":
    log("Flushing Redis database for a clean start...")
    r.flushdb()
    log("Starting Data Server with FastAPI on port 4000")
    uvicorn.run(app, host="0.0.0.0", port=4000)
