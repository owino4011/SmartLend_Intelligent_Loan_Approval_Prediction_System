from auth import db
from auth import utils
from datetime import datetime

def signup_user(email, password):
    if db.get_user_by_email(email):
        return False, "Email already registered."
    salt = utils.gen_salt()
    h = utils.hash_pw(password, salt)
    uid = db.create_user(email, h, salt, role="applicant")
    return True, {"id": uid, "email": email, "role": "applicant"}

def create_admin_account(email, password):
    if db.get_user_by_email(email):
        return False, "Email already registered."
    salt = utils.gen_salt()
    h = utils.hash_pw(password, salt)
    uid = db.create_user(email, h, salt, role="admin")
    return True, {"id": uid, "email": email, "role": "admin"}

def login_user(email, password):
    user = db.get_user_by_email(email)
    if not user:
        return False, "Account not found. Please sign up.", None

    if not user.get("salt") or not user.get("password_hash"):
        return False, "Account missing credentials. Contact admin.", None

    if utils.verify_pw(password, user["salt"], user["password_hash"]):
        db.update_last_login(email)
        return True, "Login successful", user

    return False, "Incorrect password.", None

def request_reset(email):
    user = db.get_user_by_email(email)
    if not user:
        return False, "Account not found."
    token = utils.gen_token()
    exp = utils.token_expiry()
    db.store_reset_token(email, token, exp)
    return True, token

def reset_password(email, token, new_password):
    user = db.get_user_by_email(email)
    if not user:
        return False, "Account not found."

    if user.get("reset_token") != token:
        return False, "Invalid token."

    if user.get("reset_expires_at") is None:
        return False, "No token expiry recorded. Request a new token."

    if datetime.utcnow() > user["reset_expires_at"]:
        return False, "Token expired."

    salt = utils.gen_salt()
    h = utils.hash_pw(new_password, salt)
    db.set_new_password(email, h, salt)
    db.clear_reset_token(email)

    return True, "Password updated."


