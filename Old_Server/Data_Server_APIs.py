# DataServer.py
# Simplified Data Server for encrypted file storage

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Import sessions from KMS server to validate session IDs
# from KMS_APIs import sessions

# === Setup logging ===
logging.basicConfig(
    filename='dataserver.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

def log(msg):
    print(msg)
    logging.info(msg)

# === Flask App ===
app = Flask(__name__)
CORS(app)

# In-memory store for files
files = {}  # file_name -> { encrypted_data, encrypted_aes_key }
# test version
sessions = {"68105616": "abc0975773694@gmail.com"} # sid -> email

# === Utilities ===
def validate_session():
    sid = request.headers.get('sid')
    # DEBUG
    log(f"[VALIDATE_SESSION] Incoming sid: {sid}")
    log(f"[VALIDATE_SESSION] Sessions store: {sessions}")
    if not sid or sid not in sessions:
        return False, jsonify({'error': 'invalid_session'})
    return True, None

# === API Endpoints ===

@app.route('/upload', methods=['POST'])
def upload():
    valid, err = validate_session()
    if not valid:
        return err

    data = request.get_json()
    file_name = data.get('file_name')
    encrypted_data = data.get('encrypted_data')
    encrypted_aes_key = data.get('encrypted_aes_key')

    if not file_name or not encrypted_data or not encrypted_aes_key:
        return jsonify({'error': 'missing_fields'})

    if file_name in files:
        return jsonify({'error': 'file_exists'})

    # Store encrypted file data
    files[file_name] = {
        'encrypted_data': encrypted_data,
        'encrypted_aes_key': encrypted_aes_key
    }
    log(f"[UPLOAD] Stored file '{file_name}'")
    return jsonify({'status': 'upload_success'})

@app.route('/download', methods=['GET'])
def download():
    valid, err = validate_session()
    if not valid:
        return err

    file_name = request.args.get('file_name')
    if not file_name or file_name not in files:
        return jsonify({'error': 'file_not_found'})

    record = files[file_name]
    log(f"[DOWNLOAD] Retrieved file '{file_name}'")
    return jsonify({
        'encrypted_data': record['encrypted_data'],
        'encrypted_aes_key': record['encrypted_aes_key']
    })

if __name__ == '__main__':
    log('Starting Data Server on port 4000')
    app.run(port=4000)
