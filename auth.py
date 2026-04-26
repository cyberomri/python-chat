from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, datetime
from db import get_db

auth = Blueprint("auth", __name__)
SECRET = "supersecretkey"

def create_token(username):
    return jwt.encode(
        {"user": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)},
        SECRET,
        algorithm="HS256"
    )

def verify_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])["user"]
    except:
        return None

@auth.route("/register", methods=["POST"])
def register():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users VALUES (NULL, ?, ?)",
            (data["username"], generate_password_hash(data["password"]))
        )
        conn.commit()
        return {"ok": True}
    except:
        return {"error": "user exists"}

@auth.route("/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?", (data["username"],))
    row = c.fetchone()

    if row and check_password_hash(row[0], data["password"]):
        return {"token": create_token(data["username"])}

    return {"error": "invalid"}