from flask import Flask, request, jsonify
import os

app = Flask(__name__)
messages = []

@app.route("/")
def index():
    return open("index.html").read()

@app.route("/send", methods=["GET", "POST"])
def send():
    msg = request.args.get("msg") or request.form.get("msg")
    sender = request.args.get("sender", "User")
    if msg:
        messages.append(sender + ": " + msg)
        if len(messages) > 50:
            messages.pop(0)
    return "OK"

@app.route("/messages")
def get_messages():
    html = "".join("<div style='padding:6px;margin:3px;background:" +
        ("#d0e8ff" if m.startswith("ESP32") else "#d0ffd0") +
        ";border-radius:8px'>" + m + "</div>"
        for m in messages)
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
