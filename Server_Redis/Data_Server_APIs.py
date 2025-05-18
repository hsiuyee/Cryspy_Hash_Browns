# DataServer.py
# Redis-backed Data Server for encrypted file storage

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import redis

# === Setup logging ===
logging.basicConfig(
    filename='dataserver.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

def log(msg):
    print(msg)
    logging.info(msg)

# === Redis client ===
# Assumes Redis used by KMS server stores sessions in hash 'sessions'
r = redis.Redis(host='localhost', port=6379, db=0)

# === Flask App ===
app = Flask(__name__)
CORS(app)

# === Utilities ===
# File data operations using Redis hash 'filedata:{file_name}'
def file_exists(fname):
    return r.exists(f"filedata:{fname}")

def save_file(fname, data, aes_key):
    key = f"filedata:{fname}"
    r.hset(key, mapping={
        'encrypted_data': data,
        'encrypted_aes_key': aes_key
    })

def get_file(fname):
    key = f"filedata:{fname}"
    if not r.exists(key):
        return None
    rec = r.hgetall(key)
    return {k.decode(): v.decode() for k, v in rec.items()}

# === API Endpoints ===

@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    fname = data.get('file_name')
    edata = data.get('encrypted_data')
    ekey = data.get('encrypted_aes_key')

    if not fname or not edata or not ekey:
        return jsonify({'error': 'missing_fields'})

    if file_exists(fname):
        return jsonify({'error': 'file_exists'})

    save_file(fname, edata, ekey)
    log(f"[UPLOAD] Stored file '{fname}' in Redis")
    return jsonify({'status': 'upload_success'})

@app.route('/download', methods=['GET'])
def download():
    fname = request.args.get('file_name')
    rec = get_file(fname)
    if not rec:
        return jsonify({'error': 'file_not_found'})

    log(f"[DOWNLOAD] Retrieved file '{fname}' from Redis")
    return jsonify({
        'encrypted_data': rec['encrypted_data'],
        'encrypted_aes_key': rec['encrypted_aes_key']
    })

if __name__ == '__main__':
    log('Starting Redis-backed Data Server on port 4000')
    app.run(port=4000)
