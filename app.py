from flask import Flask, request, jsonify
import os
import requests as req
import time
import anthropic
from datetime import datetime

app = Flask(__name__)

# Firebase Database URL
DB_URL = "https://esp32-chat-a33d7-default-rtdb.europe-west1.firebasedatabase.app"

# Track user activity
online_users = {}
typing_users = {}

# Constants
MESSAGE_LIMIT = 50
ONLINE_TIMEOUT = 15
TYPING_TIMEOUT = 5
AI_MESSAGE_HISTORY = 10


def load_messages():
    """Load all messages from Firebase."""
    try:
        response = req.get(DB_URL + "/messages.json", timeout=5)
        data = response.json()
        
        if not data:
            return []
        if isinstance(data, list):
            return [m for m in data if m is not None]
        if isinstance(data, dict):
            return [data[k] for k in sorted(data.keys())]
    except Exception as e:
        print(f"Error loading messages: {e}")
        return []


def save_message(msg):
    """Save a message to Firebase."""
    try:
        req.post(DB_URL + "/messages.json", json=msg, timeout=5)
    except Exception as e:
        print(f"Error saving message: {e}")


def trim_messages():
    """Keep only the last MESSAGE_LIMIT messages."""
    try:
        response = req.get(DB_URL + "/messages.json", timeout=5)
        data = response.json()
        
        if not data:
            return
        
        if isinstance(data, list):
            keys = [i for i, m in enumerate(data) if m is not None]
        else:
            keys = sorted(data.keys())
        
        if len(keys) > MESSAGE_LIMIT:
            for k in keys[:-MESSAGE_LIMIT]:
                req.delete(f"{DB_URL}/messages/{k}.json", timeout=5)
    except Exception as e:
        print(f"Error trimming messages: {e}")


def clean_online():
    """Remove inactive users from online/typing lists."""
    now = time.time()
    
    for user in list(online_users.keys()):
        if now - online_users[user] > ONLINE_TIMEOUT:
            del online_users[user]
    
    for user in list(typing_users.keys()):
        if now - typing_users[user] > TYPING_TIMEOUT:
            del typing_users[user]


def get_ai_reply(messages_history):
    """Get a reply from Claude AI using message history."""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        
        history = "\n".join([
            f"{m['sender']}: {m['text']}" 
            for m in messages_history[-AI_MESSAGE_HISTORY:]
        ])
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            system="You are Bubble, a friendly AI in a chatroom. Keep replies short and conversational. You were summoned with @Bubble.",
            messages=[{"role": "user", "content": history}]
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Error getting AI reply: {e}")
        return "Sorry, I'm having trouble thinking right now!"


@app.route("/")
def index():
    """Serve the main HTML page."""
    try:
        return open("index.html").read()
    except FileNotFoundError:
        return "Error: index.html not found", 404


@app.route("/send", methods=["GET", "POST"])def send():
    """Handle incoming messages."""
    msg = request.args.get("msg") or request.form.get("msg")
    sender = request.args.get("sender", "User")
    color = request.args.get("color", "#00b4d8")
    
    if sender in typing_users:
        del typing_users[sender]
    
    if msg:
        now = datetime.utcnow().strftime("%H:%M")
        
        save_message({
            "sender": sender,
            "text": msg,
            "color": color,
            "time": now
        })
        
        # Check if @Bubble was mentioned
        if "@Bubble" in msg or "@bubble" in msg:
            history = load_messages()
            reply = get_ai_reply(history)
            
            save_message({
                "sender": "Bubble",
                "text": reply,
                "color": "#c77dff",
                "time": datetime.utcnow().strftime("%H:%M")
            })
        
        trim_messages()
    
    return "OK"


@app.route("/ping")
def ping():
    """Update user online status and return online/typing users."""
    sender = request.args.get("sender", "")
    
    if sender:
        online_users[sender] = time.time()
    
    clean_online()
    
    return jsonify({
        "online": list(online_users.keys()),
        "typing": list(typing_users.keys())
    })


@app.route("/typing")
def typing():
    """Update user typing status."""
    sender = request.args.get("sender", "")
    
    if sender:
        typing_users[sender] = time.time()
        online_users[sender] = time.time()
    
    clean_online()
    
    return "OK"


@app.route("/messages")
def get_messages():
    """Get all messages."""
    return jsonify(load_messages())


@app.route("/manifest.json")
def manifest():
    """Serve PWA manifest."""
    try:
        return open("manifest.json").read(), 200, {"Content-Type": "application/json"}
    except FileNotFoundError:
        return "Error: manifest.json not found", 404


@app.route("/sw.js")
def sw():
    """Serve service worker."""
    try:
        return open("sw.js").read(), 200, {"Content-Type": "application/javascript"}
    except FileNotFoundError:
        return "Error: sw.js not found", 404


@app.route("/icon-192.png")
def icon192():
    """Serve 192px icon."""
    try:
        return open("icon-192.png", "rb").read(), 200, {"Content-Type": "image/png"}
    except FileNotFoundError:
        return "Error: icon-192.png not found", 404


@app.route("/icon-512.png")
def icon512():
    """Serve 512px icon."""
    try:
        return open("icon-512.png", "rb").read(), 200, {"Content-Type": "image/png"}
    except FileNotFoundError:
        return "Error: icon-512.png not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)