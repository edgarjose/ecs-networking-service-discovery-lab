from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="healthy", service="payments")


@app.get("/payment")
def payment():
    return jsonify(
        service="payments",
        status="approved",
        amount=100,
        currency="USD",
        hostname=socket.gethostname(),
        ip=socket.gethostbyname(socket.gethostname()),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
