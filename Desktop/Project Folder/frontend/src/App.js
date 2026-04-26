import { useEffect, useState } from "react";
import socket from "./socket";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [token, setToken] = useState("");

  const [receiver, setReceiver] = useState("");
  const [msg, setMsg] = useState("");

  const [chat, setChat] = useState([]);

  // receive messages
  useEffect(() => {
    socket.on("message", (data) => {
      setChat((prev) => [...prev, data]);
    });

    return () => socket.off("message");
  }, []);

  // login
  async function login() {
    const res = await fetch("http://localhost:5000/login", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        username,
        password
      })
    });

    const data = await res.json();

    if (data.token) {
      setToken(data.token);
      alert("Logged in!");
    } else {
      alert("Login failed");
    }
  }

  // send message
  function sendMessage() {
    socket.emit("message", {
      token,
      receiver,
      msg
    });

    setMsg("");
  }

return (
  <div style={{
    padding: 20,
    fontFamily: "Arial",
    maxWidth: 500,
    margin: "0 auto"
  }}>

    <h2>💬 Simple Chat App</h2>

    {/* LOGIN */}
    <div style={{
      padding: 10,
      border: "1px solid #ccc",
      borderRadius: 10,
      marginBottom: 20
    }}>
      <h3>Login</h3>

      <input
        placeholder="username"
        onChange={(e) => setUsername(e.target.value)}
        style={{ marginRight: 5 }}
      />

      <input
        placeholder="password"
        type="password"
        onChange={(e) => setPassword(e.target.value)}
        style={{ marginRight: 5 }}
      />

      <button onClick={login}>Login</button>
    </div>

    {/* CHAT BOX */}
    <div style={{
      border: "1px solid #ccc",
      borderRadius: 10,
      padding: 10
    }}>
      <h3>Chat</h3>

      <input
        placeholder="receiver"
        onChange={(e) => setReceiver(e.target.value)}
        style={{ marginRight: 5 }}
      />

      <div style={{
        height: 250,
        overflowY: "auto",
        border: "1px solid #eee",
        padding: 10,
        marginTop: 10,
        marginBottom: 10,
        background: "#fafafa"
      }}>
        {chat.map((c, i) => (
          <div key={i} style={{
            textAlign: c.sender === username ? "right" : "left",
            marginBottom: 8
          }}>
            <span style={{
              display: "inline-block",
              padding: 8,
              borderRadius: 10,
              background: c.sender === username ? "#DCF8C6" : "#fff",
              border: "1px solid #ddd"
            }}>
              <b>{c.sender}</b>: {c.msg}
            </span>
          </div>
        ))}
      </div>

      <input
        placeholder="message"
        value={msg}
        onChange={(e) => setMsg(e.target.value)}
        style={{ marginRight: 5 }}
      />

      <button onClick={sendMessage}>Send</button>
    </div>

  </div>
);
}

export default App;