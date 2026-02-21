# auth/utils.py
import hashlib
import secrets
from datetime import datetime, timedelta

def gen_salt():
    return secrets.token_hex(32)

def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        200000
    ).hex()

def verify_pw(password, salt, stored):
    return secrets.compare_digest(hash_pw(password, salt), stored)

def gen_token():
    return secrets.token_urlsafe(32)

def token_expiry():
    return datetime.utcnow() + timedelta(hours=1)







