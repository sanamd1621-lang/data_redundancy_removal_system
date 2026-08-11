from flask import Flask, render_template, request, jsonify
import sqlite3
import re
from difflib import SequenceMatcher
from datetime import datetime

app = Flask(__name__)
DB = "database.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            status TEXT NOT NULL DEFAULT 'verified',
            duplicate_of INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def normalize(value):
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]", "", value.lower().strip())

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def find_match(data):
    conn = get_db()
    rows = conn.execute("SELECT * FROM records").fetchall()
    conn.close()

    new_email = normalize(data["email"])
    new_phone = normalize(data.get("phone", ""))
    new_name = data["name"]
    new_address = data.get("address", "")

    for row in rows:
        # Strong duplicate rules
        if new_email and new_email == normalize(row["email"]):
            return row, "duplicate", 1.0

        if new_phone and new_phone == normalize(row["phone"]):
            return row, "duplicate", 1.0

        # Fuzzy comparison for possible duplicates
        name_score = similarity(new_name, row["name"])
        address_score = similarity(new_address, row["address"]) if new_address and row["address"] else 0

        if name_score >= 0.92 and address_score >= 0.80:
            score = (name_score + address_score) / 2
            return row, "duplicate", score

        # False-positive zone: looks similar, but not enough evidence
        if name_score >= 0.88 and address_score < 0.80:
            return row, "false_positive", name_score

    return None, "unique", 0.0

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/records", methods=["GET"])
def records():
    conn = get_db()
    rows = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/validate", methods=["POST"])
def validate():
    data = request.get_json() or {}

    required = ["name", "email"]
    if any(not str(data.get(x, "")).strip() for x in required):
        return jsonify({"success": False, "message": "Name and email are required."}), 400

    match, classification, score = find_match(data)

    if classification == "duplicate":
        return jsonify({
            "success": True,
            "classification": "duplicate",
            "score": round(score * 100, 2),
            "matched_record": dict(match),
            "message": "Duplicate detected. The record was NOT added."
        })

    if classification == "false_positive":
        return jsonify({
            "success": True,
            "classification": "false_positive",
            "score": round(score * 100, 2),
            "matched_record": dict(match),
            "message": "Possible similarity detected. Manual verification is recommended."
        })

    return jsonify({
        "success": True,
        "classification": "unique",
        "score": 0,
        "message": "No matching record found. The data can be added."
    })

@app.route("/records", methods=["POST"])
def add_record():
    data = request.get_json() or {}

    if not str(data.get("name", "")).strip() or not str(data.get("email", "")).strip():
        return jsonify({"success": False, "message": "Name and email are required."}), 400

    match, classification, score = find_match(data)

    if classification == "duplicate":
        return jsonify({
            "success": False,
            "classification": "duplicate",
            "message": "Duplicate data rejected. Existing record ID: " + str(match["id"])
        }), 409

    conn = get_db()
    cur = conn.execute("""
        INSERT INTO records (name, email, phone, address, status, duplicate_of, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"].strip(),
        data["email"].strip(),
        data.get("phone", "").strip(),
        data.get("address", "").strip(),
        "verified" if classification == "unique" else "manual_review",
        match["id"] if match else None,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    record_id = cur.lastrowid
    conn.close()

    return jsonify({
        "success": True,
        "id": record_id,
        "classification": classification,
        "message": "Unique verified data added successfully."
    })

@app.route("/records/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    conn = get_db()
    conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Record deleted."})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
