import requests
import sys

API_BASE = "http://127.0.0.1:3000"


def prompt(msg):
    return input(msg).strip()


def register():
    email = prompt("Enter email to register: ")
    pw = prompt("Enter password: ")
    res = requests.post(f"{API_BASE}/register", json={"email": email, "password_hash": pw})
    print("Register response:", res.json())
    return email


def verify_email(email):
    otp = prompt(f"Enter OTP sent to {email}: ")
    res = requests.post(f"{API_BASE}/verify_email", json={"email": email, "otp": otp})
    print("Verify email response:", res.json())


def login():
    email = prompt("Enter email to login: ")
    pw = prompt("Enter password: ")
    res = requests.post(f"{API_BASE}/login", json={"email": email, "password_hash": pw})
    print("Login response:", res.json())
    return email


def verify_otp(email):
    otp = prompt(f"Enter login OTP sent to {email}: ")
    res = requests.post(f"{API_BASE}/verify_otp", json={"email": email, "otp": otp})
    print("Verify OTP response:", res.json())
    if res.json().get("status") == "login_success":
        sid = res.json().get("sid")
        print(f"Received sid: {sid}")
        return sid
    return None


def get_public_key(sid):
    filename = prompt("Enter filename for public key generation: ")
    res = requests.post(
        f"{API_BASE}/get_public_key",
        json={"file_name": filename},
        headers={"sid": sid}
    )
    print("Get public key response:", res.json())


def get_private_key(sid):
    filename = prompt("Enter filename to retrieve private key: ")
    res = requests.post(
        f"{API_BASE}/get_private_key",
        json={"file_name": filename},
        headers={"sid": sid}
    )
    print("Get private key response:", res.json())


def grant_access(sid):
    filename = prompt("Enter filename to grant access: ")
    friend = prompt("Enter friend email: ")
    res = requests.post(
        f"{API_BASE}/grant_access",
        json={"file_name": filename, "friend_email": friend},
        headers={"sid": sid}
    )
    print("Grant access response:", res.json())


def main():
    actions = {
        "1": ("Register", register),
        "2": ("Verify Email", verify_email),
        "3": ("Login", login),
        "4": ("Verify OTP", verify_otp),
        "5": ("Get Public Key", get_public_key),
        "6": ("Get Private Key", get_private_key),
        "7": ("Grant Access", grant_access),
    }

    sid = None
    email = None

    while True:
        print("\nAvailable actions:")
        for k, v in actions.items():
            print(f"{k}. {v[0]}")
        print("q. Quit")

        choice = prompt("Select action: ")
        if choice == 'q':
            sys.exit(0)
        if choice in actions:
            name, func = actions[choice]
            print(f"--- {name} ---")
            if name == "Register":
                email = func()
            elif name == "Verify Email":
                if email:
                    func(email)
                else:
                    print("Please register first.")
            elif name == "Login":
                email = func()
            elif name == "Verify OTP":
                if email:
                    sid = func(email)
                else:
                    print("Please login first.")
            else:
                if sid:
                    func(sid)
                else:
                    print("Please complete login and OTP verification first.")
        else:
            print("Invalid choice.")

if __name__ == '__main__':
    main()
