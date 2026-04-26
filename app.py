import os
from dotenv import load_dotenv
from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- AUTH (simple demo login) ----------------
users = {
    "john": "123",
    "mike": "123"
}

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]

    if username in users and users[username] == password:
        token = jwt.encode(
            {
                "user": username,
                "exp": datetime.utcnow() + timedelta(hours=24)
            },
            SECRET_KEY,
            algorithm="HS256"
        )
        return {"token": token}

    return {"error": "invalid login"}, 401


# ---------------- VERIFY TOKEN ----------------
def verify(token):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data["user"]
    except:
        return None


# ---------------- CHAT ----------------
@socketio.on("message")
def handle_message(data):
    token = data.get("token")
    user = verify(token)

    if not user:
        return

    emit("message", {
        "sender": user,
        "receiver": data.get("receiver"),
        "msg": data.get("msg"),
        "time": datetime.now().strftime("%H:%M")
    }, broadcast=True)


# ---------------- RUN ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)