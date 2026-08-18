import base64
import os
import sqlite3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, jsonify, request

app = Flask(__name__)

# =========================================================================
# LAYER 1: AES-256 ENCRYPTION & DECRYPTION UTILITIES
# =========================================================================
# Ensure key is exactly 32 bytes for AES-256
AES_SECRET_KEY = b"12345678901234567890123456789012"


def encrypt_data(plain_text: str) -> str:
    """Encrypts plaintext string using AES-256-CBC and returns Base64 encoded string."""
    iv = os.urandom(16)
    cipher = AES.new(AES_SECRET_KEY, AES.MODE_CBC, iv)
    padded_data = pad(plain_text.encode("utf-8"), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_data)
    # Combine IV and ciphertext for storage/transmission
    return base64.b64encode(iv + encrypted_bytes).decode("utf-8")


def decrypt_data(cipher_text_b64: str) -> str:
    """Decrypts Base64 encoded AES-256-CBC payload back to plaintext."""
    data = base64.b64decode(cipher_text_b64)
    iv = data[:16]
    encrypted_bytes = data[16:]
    cipher = AES.new(AES_SECRET_KEY, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(encrypted_bytes)
    return unpad(decrypted_padded, AES.block_size).decode("utf-8")


# =========================================================================
# DATABASE SETUP
# =========================================================================
def init_db():
    """Creates SQLite database and table if they do not exist."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS secure_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensitive_info TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


# =========================================================================
# FLASK ROUTES
# =========================================================================
@app.route("/")
def home():
    """Root endpoint to verify the server is running."""
    return jsonify(
        {
            "status": "success",
            "message": "Flask AES-256 Encryption API is running successfully!",
        }
    )


@app.route("/encrypt", methods=["POST"])
def encrypt_endpoint():
    """Receives JSON with 'data', encrypts it, and saves to SQLite."""
    payload = request.get_json()
    if not payload or "data" not in payload:
        return jsonify({"error": "Missing 'data' field in request body"}), 400

    plain_text = payload["data"]
    encrypted_text = encrypt_data(plain_text)

    # Store encrypted string in database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO secure_data (sensitive_info) VALUES (?)", (encrypted_text,)
    )
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "id": record_id,
                "message": "Data encrypted and stored successfully.",
                "encrypted_data": encrypted_text,
            }
        ),
        201,
    )


@app.route("/decrypt/<int:record_id>", methods=["GET"])
def decrypt_endpoint(record_id):
    """Fetches encrypted data from SQLite by ID and decrypts it."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sensitive_info FROM secure_data WHERE id = ?", (record_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Record not found"}), 404

    encrypted_text = row[0]
    decrypted_text = decrypt_data(encrypted_text)

    return jsonify(
        {
            "id": record_id,
            "encrypted_data": encrypted_text,
            "decrypted_data": decrypted_text,
        }
    )


# =========================================================================
# APPLICATION ENTRYPOINT
# =========================================================================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)