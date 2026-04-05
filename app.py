from flask import Flask, request, jsonify
import os
import requests as req
import json
import time
import anthropic

from datetime import datetime

app = Flask(__name__)

DB_URL = "https://esp32-chat-a33d7-default-rtdb.europe-west1.firebasedatabase.app"

online_users = {}
typing_users = {}

def load_messages():
    try:
        r = req.get(DB_URL + "/messages.json")
        data = r.json()
        if not data:
            return []
        if isinstance(data, list):
            return [m for m in data if m is not None]
        if isinstance(data, dict):
            return [data[k] for k in sorted(data.keys())]
    except:
        return []
    return []

def save_message(msg):
    try:
        req.post(DB_URL + "/messages.json", json=msg)
    except:
        pass

def trim_messages():
    try:
        r = req.get(DB_URL + "/messages.json")
        data = r.json()
        if not data:
            return
        if isinstance(data, list):
            keys = [i for i, m in enumerate(data) if m is not None]
        else:
            keys = sorted(data.keys())
        if len(keys) > 50:
            for k in keys[:-50]:
                req.delete(DB_URL + "/messages/" + str(k) + ".json")
    except:
        pass

def clean_online():
    now = time.time()
    for u in list(online_users.keys()):
        if now - online_users[u] > 15:
            del online_users[u]
    for u in list(typing_users.keys()):
        if now - typing_users[u] > 5:
            del typing_users[u]

@app.route("/")
def index():
    return open("index.html").read()

@app.route("/send", methods=["GET", "POST"])
def send():
    msg = request.args.get("msg") or request.form.get("msg")
    sender = request.args.get("sender", "User")
    color = request.args.get("color", "#00b4d8")
    if sender in typing_users:
        del typing_users[sender]
    if msg:
        now = datetime.utcnow().strftime("%H:%M")
        save_message({"sender": sender, "text": msg, "color": color, "time": now})
        trim_messages()
    return "OK"

@app.route("/ping")
def ping():
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
    sender = request.args.get("sender", "")
    if sender:
        typing_users[sender] = time.time()
        online_users[sender] = time.time()
    clean_online()
    return "OK"

@app.route("/messages")
def get_messages():
    return jsonify(load_messages())

@app.route("/manifest.json")
def manifest():
    return open("manifest.json").read(), 200, {"Content-Type": "application/json"}

@app.route("/sw.js")
def sw():
    return open("sw.js").read(), 200, {"Content-Type": "application/javascript"}

@app.route("/icon-192.png")
def icon192():
    return open("icon-192.png", "rb").read(), 200, {"Content-Type": "image/png"}

@app.route("/icon-512.png")
def icon512():
    return open("icon-512.png", "rb").read(), 200, {"Content-Type": "image/png"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
