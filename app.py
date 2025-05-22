from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from dotenv import load_dotenv
import csv
import io
import hashlib
import uuid
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database config
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', 5432)

# Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    return conn

# Create table if not exists
with get_db_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id VARCHAR(100) PRIMARY KEY,
            full_name VARCHAR(100),
            pan VARCHAR(20) UNIQUE,
            dob VARCHAR(20),
            phone VARCHAR(20),
            loan_amount VARCHAR(20),
            cibil_score INT,
            status VARCHAR(20)
        )
        """)
        conn.commit()

# Fixed CIBIL generator based on PAN
def generate_fixed_cibil(pan):
    hash_val = int(hashlib.sha256(pan.encode()).hexdigest(), 16)
    return 300 + (hash_val % 601)  # Range: 300 to 900

# Phone number cleaner
def fix_phone(phone):
    digits = re.sub(r'\D', '', phone)
    return digits[-10:] if len(digits) >= 10 else None

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT version();')
    db_version = cur.fetchone()
    cur.close()
    conn.close()
    return f'Connected to: {db_version}'


@app.route('/apply', methods=['POST'])
def apply():
    try:
        data = request.json

        # Basic validation
        full_name = str(data.get('full_name', "")).strip()
        pan = str(data.get('pan', "")).strip().upper()
        dob = str(data.get('dob', "")).strip()
        phone = fix_phone(str(data.get('phone', "")))
        loan_amount = str(data.get('loan_amount', "")).strip()



        if not phone:
            return jsonify({"status": "skipped", "reason": "Invalid phone number"}), 400

        if not (full_name and pan and dob and phone and loan_amount):
            return jsonify({"status": "skipped", "reason": "Missing essential fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE pan = %s", (pan,))
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return jsonify({
                "status": "duplicate",
                "reason": "Customer already exists",
                "existing_customer_id": existing[0],
                "cibil_score": existing[6],
                "loan_status": existing[7]
            })

        cibil = generate_fixed_cibil(pan)
        status = "Approved" if cibil >= 750 else "Rejected"
        customer_id = str(uuid.uuid4())

        cursor.execute("""
        INSERT INTO customers (id, full_name, pan, dob, phone, loan_amount, cibil_score, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            customer_id, full_name, pan, dob, phone, loan_amount, cibil, status
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "added",
            "customer_id": customer_id,
            "cibil_score": cibil,
            "loan_status": status
        })
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/allApplications', methods=['GET'])
def get_all():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    rows = cursor.fetchall()
    keys = ["id", "full_name", "pan", "dob", "phone", "loan_amount", "cibil_score", "status"]
    result = [dict(zip(keys, row)) for row in rows]
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/get_customer/<customer_id>', methods=['GET'])
def get_customer_by_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        keys = ["id", "full_name", "pan", "dob", "phone", "loan_amount", "cibil_score", "status"]
        return jsonify(dict(zip(keys, row)))
    else:
        return jsonify({"message": "Customer not found"}), 404


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)

    # Fix BOM and strip headers
    reader.fieldnames = [name.strip().replace('\ufeff', '') for name in reader.fieldnames]

    added = 0
    skipped_duplicates = 0
    skipped_missing = 0
    skipped_entries = []

    conn = get_db_connection()
    cursor = conn.cursor()

    for row in reader:
        full_name = row.get("full_name", "").strip()
        pan = row.get("pan", "").strip().upper()
        dob = row.get("dob", "").strip()
        phone = fix_phone(row.get("phone", ""))
        loan_amount = row.get("loan_amount", "").strip()

        if not phone:
            skipped_missing += 1
            skipped_entries.append({**row, "reason": "Invalid phone number"})
            continue

        if not (full_name and pan and dob and phone and loan_amount):
            skipped_missing += 1
            skipped_entries.append({**row, "reason": "Missing essential fields"})
            continue

        cursor.execute("SELECT * FROM customers WHERE pan = %s", (pan,))
        if cursor.fetchone():
            skipped_duplicates += 1
            skipped_entries.append({**row, "reason": "Duplicate PAN"})
            continue

        cibil = generate_fixed_cibil(pan)
        status = "Approved" if cibil >= 750 else "Rejected"
        customer_id = str(uuid.uuid4())

        cursor.execute("""
        INSERT INTO customers (id, full_name, pan, dob, phone, loan_amount, cibil_score, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            customer_id,
            full_name,
            pan,
            dob,
            phone,
            loan_amount,
            cibil,
            status
        ))
        added += 1

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "added": added,
        "skipped_duplicates": skipped_duplicates,
        "skipped_missing": skipped_missing,
        "skipped_entries": skipped_entries
    })

@app.route('/download_cleaned_csv', methods=['GET'])
def download_cleaned_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    headers = ["id", "full_name", "pan", "dob", "phone", "loan_amount", "cibil_score", "status"]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return (
        output.getvalue(),
        200,
        {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename="cleaned_loan_data.csv"',
        }
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)   