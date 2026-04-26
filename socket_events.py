from flask_socketio import emit, join_room
from db import get_db
from datetime import datetime
import jwt

SECRET = "CHANGE_THIS_TO_ENV_SECRET"

def verify_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])["user"]
    except:
        return None

def room(a, b):
    return "__".join(sorted([a, b]))

def register_socket(socketio):

    @socketio.on("message")
    def handle_message(data):
        user = verify_token(data.get("token"))
        if not user:
            return  # reject silently

        receiver = data.get("receiver")
        msg = data.get("msg")

        conn = get_db()
        c = conn.cursor()

        c.execute("""
            INSERT INTO messages (sender, receiver, msg, time)
            VALUES (?, ?, ?, ?)
        """, (user, receiver, msg, datetime.now().strftime("%H:%M")))

        conn.commit()

        emit("message", {
            "sender": user,   # SERVER TRUSTED
            "receiver": receiver,
            "msg": msg,
            "time": datetime.now().strftime("%H:%M")
        }, broadcast=True)