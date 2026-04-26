import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import jwt
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Use SQLite (simple production starter DB)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

# ---------------- DATABASE ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# ---------------- INIT DB ----------------
@app.before_first_request
def create_tables():
    db.create_all()


# ---------------- AUTH ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    user = User(username=data["username"], password=hashed_pw)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()

    if not user or not bcrypt.check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {
            "user": user.username,
            "exp": datetime.utcnow() + timedelta(hours=24)
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return jsonify({"token": token})


# ---------------- TOKEN CHECK ----------------
def verify_token(token):
    try:
        decoded = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return decoded["user"]
    except:
        return None


# ---------------- SOCKET AUTH ----------------
@socketio.on("connect")
def connect():
    token = request.args.get("token")
    user = verify_token(token)

    if not user:
        disconnect()


# ---------------- CHAT ----------------
@socketio.on("message")
def handle_message(data):
    user = verify_token(data.get("token"))
    if not user:
        return

    emit("message", {
        "sender": user,
        "msg": data["msg"],
        "time": datetime.now().strftime("%H:%M")
    }, broadcast=True)


# ---------------- RUN ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
