"""
Backend for OTP Login System using Brevo Email API.
Fully compatible with Render hosting.
"""

import os
import random
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

# ---------------------------
# IN-MEMORY STORAGE
# ---------------------------
otp_store = {}
users_store = {}

# ---------------------------
# BREVO API KEY
# ---------------------------
BREVO_API_KEY = os.getenv("BREVO_API_KEY")  # Set this in Render environment


def send_otp_email(to_email, otp):
    """Send OTP using Brevo API."""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": "EduShare", "email": "no-reply@edushare.com"},
        "to": [{"email": to_email}],
        "subject": "Your OTP Code",
        "htmlContent": f"<p>Your OTP is: <strong>{otp}</strong></p>"
    }

    response = requests.post(url, json=data, headers=headers)
    print("Brevo Response:", response.text)

    if response.status_code not in [200, 201]:
        raise Exception("Failed to send OTP email")


# ---------------------------
# ROUTES
# ---------------------------

@app.route("/send-otp", methods=["POST"])
def send_otp():
    email = request.json.get("email")

    if not email:
        return jsonify({"message": "Email is required"}), 400

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    try:
        send_otp_email(email, otp)
        return jsonify({"message": "OTP sent successfully!"})
    except Exception as e:
        print("ERROR sending OTP:", e)
        return jsonify({"message": "Failed to send OTP"}), 500


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data.get("email")
    user_otp = data.get("otp")
    name = data.get("name")
    password = data.get("password")

    stored_otp = otp_store.get(email)

    if stored_otp and stored_otp == user_otp:
        users_store[email] = {
            "name": name,
            "password": password
        }

        del otp_store[email]

        return jsonify({"status": "verified", "message": "Account created!"})

    return jsonify({"status": "invalid", "message": "Wrong OTP"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if email in users_store and users_store[email]["password"] == password:
        return jsonify({"message": "success", "name": users_store[email]["name"]})

    return jsonify({"error": "Invalid email or password"}), 401


@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 5000))
