import base64
import os
import sqlite3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, jsonify, request

app = Flask(__name__)

AES_SECRET_KEY = b"12345678901234567890123456789012"
DB_NAME = "database.db"

# ==============================================================================
# DATABASE SETUP
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            encrypted_capability TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# AES UTILITIES
# ==============================================================================
def encrypt_data(plain_text: str) -> str:
    iv = os.urandom(16)
    cipher = AES.new(AES_SECRET_KEY, AES.MODE_CBC, iv)
    padded_data = pad(plain_text.encode("utf-8"), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_data)
    return base64.b64encode(iv + encrypted_bytes).decode("utf-8")

def decrypt_data(cipher_text_b64: str) -> str:
    data = base64.b64decode(cipher_text_b64)
    iv = data[:16]
    encrypted_bytes = data[16:]
    cipher = AES.new(AES_SECRET_KEY, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(encrypted_bytes)
    return unpad(decrypted_padded, AES.block_size).decode("utf-8")

# ==============================================================================
# ROUTES
# ==============================================================================

     # Add this right above @app.route("/api/v1/user")
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "Welcome to the Secure Data Detection API!",
        "endpoints": {
            "save_user": "POST /api/v1/user",
            "get_decrypted_user": "GET /api/v1/user/decrypt/<user_id>"
        }
    })
# 1. Save Encrypted User Data
@app.route("/api/v1/user", methods=["POST"])
def user_endpoint():
    data = request.get_json()
    username = data.get("username")
    capability_code = data.get("capability_code")

    encrypted_cap = encrypt_data(capability_code)

    # Save to SQLite database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, encrypted_capability) VALUES (?, ?)",
        (username, encrypted_cap)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "id": user_id,
        "username": username,
        "encrypted_capability": encrypted_cap
    })

# 2. Retrieve & Decrypt User Data
@app.route("/api/v1/user/decrypt/<int:user_id>", methods=["GET"])
def get_decrypted_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, encrypted_capability FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User record not found"}), 404

    record_id, username, encrypted_cap = row
    decrypted_cap = decrypt_data(encrypted_cap)

    return jsonify({
        "id": record_id,
        "username": username,
        "encrypted_capability": encrypted_cap,
        "decrypted_capability": decrypted_cap
    })

    return jsonify({
        "id": record_id,
        "username": username,
        "encrypted_capability": encrypted_cap,
        "decrypted_capability": decrypted_cap
    })

# 3. Retrieve All Users from Database
@app.route("/api/v1/users", methods=["GET"])
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, encrypted_capability FROM users")
    rows = cursor.fetchall()
    conn.close()

    users_list = []
    for row in rows:
        users_list.append({
            "id": row[0],
            "username": row[1],
            "encrypted_capability": row[2]
        })

    return jsonify({"total": len(users_list), "users": users_list})

if __name__ == "__main__":
    app.run(debug=True, port=5000)