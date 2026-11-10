from flask import Flask, jsonify
import os
import requests
import socket

app = Flask(__name__)

PAYMENTS_URL = os.getenv(
    "PAYMENTS_URL",
    "http://payments.lab.internal:5000"
)

@app.get("/health")
def health():
    return jsonify(
        status="healthy",
        service="orders"
    )

@app.get("/checkout")
def checkout():
    try:
        response = requests.get(
            f"{PAYMENTS_URL}/payment",
            timeout=5
        )
        response.raise_for_status()

        return jsonify(
            service="orders",
            status="completed",
            order_id="ORDER-1001",
            hostname=socket.gethostname(),
            payment=response.json()
        )

    except requests.RequestException as exc:
        app.logger.error("Payment request failed: %s", exc)
        return jsonify(
            service="orders",
            status="failed",
            error="Payment service unavailable"
        ), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
