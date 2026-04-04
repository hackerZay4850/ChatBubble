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
    color = request.args.get("color", "#00b4d8")
    if msg:
        messages.append({"sender": sender, "text": msg, "color": color})
        if len(messages) > 50:
            messages.pop(0)
    return "OK"

@app.route("/messages")
def get_messages():
    return jsonify(messages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
