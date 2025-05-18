# ds_api_cli_test.py
# Interactive CLI client for testing Data Server APIs

import requests
import sys

API_BASE = "http://127.0.0.1:4000"


def prompt(msg):
    return input(msg).strip()


def get_session_id():
    return prompt("Enter sid: ")


def upload_file(sid):
    filename = prompt("Enter filename to upload: ")
    data = prompt("Enter encrypted data: ")
    key = prompt("Enter encrypted AES key: ")
    res = requests.post(
        f"{API_BASE}/upload",
        json={"file_name": filename, "encrypted_data": data, "encrypted_aes_key": key},
        headers={"sid": sid}
    )
    print("Upload response:", res.json())


def download_file(sid):
    filename = prompt("Enter filename to download: ")
    res = requests.get(
        f"{API_BASE}/download",
        params={"file_name": filename},
        headers={"sid": sid}
    )
    print("Download response:", res.json())


def main():
    actions = {
        "1": ("Upload File", upload_file),
        "2": ("Download File", download_file),
    }

    while True:
        print("\nAvailable actions:")
        for k, v in actions.items():
            print(f"{k}. {v[0]}")
        print("q. Quit")

        choice = prompt("Select action: ")
        if choice == 'q':
            sys.exit(0)
        if choice in actions:
            sid = get_session_id()
            print(f"Using sid: {sid}")
            _, func = actions[choice]
            func(sid)
        else:
            print("Invalid choice.")

if __name__ == '__main__':
    main()
