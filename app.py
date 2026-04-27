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

# ---------------- CONFIG ----------------
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------- INIT EXTENSIONS ----------------
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80))
    msg = db.Column(db.Text)
    time = db.Column(db.String(10))


# ---------------- CREATE TABLES (FLASK 3 FIX) ----------------
with app.app_context():
    db.create_all()


# ---------------- AUTH ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if User.query.filter_by(username=data.get("username")).first():
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(
        data.get("password")
    ).decode("utf-8")

    user = User(
        username=data.get("username"),
        password=hashed_pw
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created"}), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(username=data.get("username")).first()

    if not user or not bcrypt.check_password_hash(user.password, data.get("password")):
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


# ---------------- TOKEN VERIFY ----------------
def verify_token(token):
    try:
        decoded = jwt.decode(
            token,
            app.config["SECRET_KEY"],
            algorithms=["HS256"]
        )
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

    msg_text = data.get("msg")

    message = Message(
        sender=user,
        msg=msg_text,
        time=datetime.now().strftime("%H:%M")
    )

    db.session.add(message)
    db.session.commit()

    emit("message", {
        "sender": user,
        "msg": msg_text,
        "time": message.time
    }, broadcast=True)


# ---------------- GET MESSAGES ----------------
@app.route("/messages", methods=["GET"])
def get_messages():
    messages = Message.query.all()

    return jsonify([
        {
            "sender": m.sender,
            "msg": m.msg,
            "time": m.time
        }
        for m in messages
    ])


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Secure Chat Server Running 🚀"


# ---------------- RUN ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
