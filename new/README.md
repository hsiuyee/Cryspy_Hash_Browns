# Secure File Storage System

This repository contains two FastAPI-based microservices for secure file storage and key management:

1. **KMS Server** (`KMS_APIs_fastapi.py`):
   - Handles user registration, login with email-based OTP (2FA), session management, and RSA key pair generation.
   - Manages file access control, granting and verifying permissions for file encryption/decryption keys.

2. **Data Server** (`Data_Server_APIs_fastapi.py`):
   - Provides encrypted file storage using AES for data encryption.
   - Stores encrypted data, AES key, and IV in Redis.
   - Offers endpoints to upload, download, and list encrypted files.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Servers](#running-the-servers)
- [API Reference](#api-reference)
  - [KMS Server Endpoints](#kms-server-endpoints)
  - [Data Server Endpoints](#data-server-endpoints)
- [Logging](#logging)
- [Redis Database](#redis-database)
- [Security Considerations](#security-considerations)
- [License](#license)

---

## Prerequisites

- Python 3.8+
- Redis server (running locally on default port `6379`)
- Access to an SMTP server for sending OTP emails

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hsiuyee/Cryspy_Hash_Browns.git
   cd Cryspy_Hash_Browns/new
   ````

2. **Create a virtual environment and install dependencies**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Start Redis** (if not already running):

   ```bash
   redis-server
   ```

## Configuration

Copy `.env.example` to `.env` and update the following variables:

```ini
# SMTP settings for KMS email OTP
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SENDER_EMAIL=you@example.com
SENDER_PASS=your_smtp_password

# Redis connection (default uses localhost:6379)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Running the Servers

Each service flushes its Redis database on startup for a clean state.

### 1. KMS Server (Port 3000)

```bash
# under Cryspy_Hash_Browns/new
python3 ./KMS_APIs_fastapi.py
```

### 2. Data Server (Port 4000)

```bash
# under Cryspy_Hash_Browns/new
python3 ./Data_Server_APIs_fastapi.py
```

## API Reference

### KMS Server Endpoints

| Endpoint           | Method | Description                                                         | Returns (JSON)                                                                                                                                                 |
| ------------------ | ------ | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/register`        | POST   | Register a new user (sends OTP email).                              | `code: 200, message: "registration_pending"`<br/>`code: 400, message: "user_exists"`                                                                           |
| `/verify_register` | POST   | Verify registration OTP and create user account.                    | `code: 200, message: "registration_success"`<br/>`code: 400, message: "no_pending_registration"`<br/>`code: 401, message: "otp_failed"`                        |
| `/login`           | POST   | Request login OTP (2FA).                                            | `code: 200, message: "login_otp_sent"`<br/>`code: 401, message: "login_failed"`                                                                                |
| `/verify_login`    | POST   | Verify login OTP and return session ID (`sid`).                     | `code: 200, message: "login_success", sid: <session_id>`<br/>`code: 401, message: "otp_failed"`                                                                |
| `/get_public_key`  | POST   | Generate and store RSA key pair for a file (requires `sid`).        | `code: 200, message: "public_key_saved", kms_public_key: <base64>`<br/>`code: 400, message: "file_exists"`<br/>`code: 403, message: "invalid_session"`         |
| `/get_private_key` | POST   | Retrieve private key for a file (requires access and `sid`).        | `code: 200, message: "private_key_retrieved", kms_private_key: <base64>`<br/>`code: 400, message: "access_denied"`<br/>`code: 403, message: "invalid_session"` |
| `/grant_access`    | POST   | Grant key access to another registered user (requires owner `sid`). | `code: 200, message: "grant_success"`<br/>`code: 400, message: "permission_denied"`<br/>`code: 403, message: "invalid_session"`                                |

#### Authentication

All protected endpoints (`get_public_key`, `get_private_key`, `grant_access`) require a header:

```
sid: <session_id>
```

#### Example: Register

```bash
curl -X POST http://localhost:3000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"P@ssw0rd"}'
```

#### Example: Verify Registration

```bash
curl -X POST http://localhost:3000/verify_register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","otp":"123456"}'
```

#### Example: Login (Request OTP)

```bash
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"P@ssw0rd"}'
```

#### Example: Verify Login

```bash
curl -X POST http://localhost:3000/verify_login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","otp":"654321"}'
```

#### Example: Generate Public Key

```bash
curl -X POST http://localhost:3000/get_public_key \
  -H "Content-Type: application/json" \
  -H "sid: <your_session_id>" \
  -d '{"file_name":"report.pdf"}'
```

#### Example: Retrieve Private Key

```bash
curl -X POST http://localhost:3000/get_private_key \
  -H "Content-Type: application/json" \
  -H "sid: <your_session_id>" \
  -d '{"file_name":"report.pdf"}'
```

#### Example: Grant Access

```bash
curl -X POST http://localhost:3000/grant_access \
  -H "Content-Type: application/json" \
  -H "sid: <owner_session_id>" \
  -d '{"file_name":"report.pdf","friend_email":"bob@example.com"}'
```

### Data Server Endpoints

| Endpoint      | Method | Description                                     | Returns (JSON)                                                                                                                                        |
| ------------- | ------ | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/upload`     | POST   | Upload an encrypted file with its AES envelope. | `code: 200, message: "upload_success"`<br/>`code: 400, message: "missing_fields"`<br/>`code: 409, message: "file_exists"`                             |
| `/download`   | GET    | Download encrypted data, AES key, and IV.       | `code: 200, encrypted_data: <base64>, encrypted_aes_key: <base64>, encrypted_aes_initial_vector: <base64>`<br/>`code: 404, message: "file_not_found"` |
| `/list_files` | GET    | List all stored file names.                     | `code: 200, files: [<file_name>, ...], message: "list_files_success"`                                        

#### Example: Upload

```bash
curl -X POST http://localhost:4000/upload \
  -H "Content-Type: application/json" \
  -d '{
        "file_name":"report.pdf",
        "encrypted_data":"<base64-data>",
        "encrypted_aes_key":"<base64-key>",
        "encrypted_aes_initial_vector":"<base64-iv>"
      }'
```

#### Example: Download

```bash
curl "http://localhost:4000/download?file_name=report.pdf"
```

#### Example: List files

```bash
curl "http://localhost:4000/list_files"
```

## Logging

* **KMS Server** logs to `kms.log`
* **Data Server** logs to `dataserver.log`

Each request and important state change is logged with timestamps and log levels.

## Redis Database

* All state (users, sessions, file keys, file data) is stored in Redis.
* Data is flushed on server startup; adjust as needed for persistence in production.

## Security Considerations

* **Passwords** are hashed with `bcrypt`.
* **2FA** is enforced via email OTP for both registration and login.
* **RSA (2048-bit)** for file key pairs, **AES** for file content.
* Ensure SMTP credentials are secured and Redis access is restricted.


