from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from dotenv import load_dotenv
import csv
import io
import hashlib
import uuid

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
    return 300 + (hash_val % 601)  # 300 to 900

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
    data = request.json
    pan = data.get('pan')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE pan = %s", (pan,))
    existing = cursor.fetchone()

    if existing:
        cursor.close()
        conn.close()
        return jsonify({"message": "Customer already exists", "status": existing[7], "cibil_score": existing[6]})

    cibil = generate_fixed_cibil(pan)
    status = "Approved" if cibil >= 750 else "Rejected"
    customer_id = str(uuid.uuid4())

    cursor.execute("""
    INSERT INTO customers (id, full_name, pan, dob, phone, loan_amount, cibil_score, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        customer_id,
        data.get('full_name'),
        pan,
        data.get('dob'),
        data.get('phone'),
        data.get('loan_amount'),
        cibil,
        status
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"customer_id": customer_id, "status": status, "cibil_score": cibil})

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

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)

    added, skipped = 0, 0

    conn = get_db_connection()
    cursor = conn.cursor()

    for row in reader:
        pan = row.get("pan")
        cursor.execute("SELECT * FROM customers WHERE pan = %s", (pan,))
        if cursor.fetchone():
            skipped += 1
            continue

        cibil = generate_fixed_cibil(pan)
        status = "Approved" if cibil >= 750 else "Rejected"
        customer_id = str(uuid.uuid4())

        cursor.execute("""
        INSERT INTO customers (id, full_name, pan, dob, phone, loan_amount, cibil_score, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            customer_id,
            row.get('full_name'),
            pan,
            row.get('dob'),
            row.get('phone'),
            row.get('loan_amount'),
            cibil,
            status
        ))
        added += 1

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"added": added, "skipped_duplicates": skipped})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)






# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import psycopg2
# from flask import Flask
# import mysql.connector
# from dotenv import load_dotenv
# import csv
# import io
# import hashlib
# import uuid

# # Load environment variables
# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# app = Flask(__name__)

# # Load environment variables from Render or .env
# DB_HOST = os.environ.get('DB_HOST')
# DB_NAME = os.environ.get('DB_NAME')
# DB_USER = os.environ.get('DB_USER')
# DB_PASSWORD = os.environ.get('DB_PASSWORD')
# DB_PORT = os.environ.get('DB_PORT', 5432)

# # Connect to PostgreSQL
# def get_db_connection():
#     conn = psycopg2.connect(
#         host=DB_HOST,
#         database=DB_NAME,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         port=DB_PORT
#     )
#     return conn

# @app.route('/')
# def index():
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute('SELECT version();')
#     db_version = cur.fetchone()
#     cur.close()
#     conn.close()
#     return f'Connected to: {db_version}'

# # MySQL connection
# db = mysql.connector.connect(
#     host=os.getenv("DB_HOST"),
#     user=os.getenv("DB_USER"),
#     password=os.getenv("DB_PASSWORD"),
#     database=os.getenv("DB_NAME")
# )
# cursor = db.cursor()

# # Create table if not exists
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS customers (
#     id VARCHAR(100) PRIMARY KEY,
#     full_name VARCHAR(100),
#     pan VARCHAR(20) UNIQUE,
#     dob VARCHAR(20),
#     phone VARCHAR(20),
#     loan_amount VARCHAR(20),
#     cibil_score INT,
#     status VARCHAR(20)
# )
# """)
# db.commit()

# # Fixed CIBIL generator based on PAN
# def generate_fixed_cibil(pan):
#     hash_val = int(hashlib.sha256(pan.encode()).hexdigest(), 16)
#     return 300 + (hash_val % 601)  # 300 to 900

# @app.route('/apply', methods=['POST'])
# def apply():
#     data = request.json
#     pan = data.get('pan')
    
#     # Check for existing PAN
#     cursor.execute("SELECT * FROM customers WHERE pan = %s", (pan,))
#     existing = cursor.fetchone()
#     if existing:
#         return jsonify({"message": "Customer already exists", "status": existing[6], "cibil_score": existing[5]})

#     # Assign fixed CIBIL
#     cibil = generate_fixed_cibil(pan)
#     status = "Approved" if cibil >= 750 else "Rejected"
#     customer_id = str(uuid.uuid4())

#     cursor.execute("""
#     INSERT INTO customers (id, full_name, pan, dob, phone, loan_amount, cibil_score, status)
#     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#     """, (
#         customer_id,
#         data.get('full_name'),
#         pan,
#         data.get('dob'),
#         data.get('phone'),
#         data.get('loan_amount'),
#         cibil,
#         status
#     ))
#     db.commit()

#     return jsonify({"customer_id": customer_id, "status": status, "cibil_score": cibil})

# @app.route('/allApplications', methods=['GET'])
# def get_all():
#     cursor.execute("SELECT * FROM customers")
#     rows = cursor.fetchall()
#     keys = ["id", "full_name", "pan", "dob", "phone", "loan_amount", "cibil_score", "status"]
#     return jsonify([dict(zip(keys, row)) for row in rows])

# @app.route('/upload_csv', methods=['POST'])
# def upload_csv():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files['file']
#     stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
#     reader = csv.DictReader(stream)

#     added, skipped = 0, 0
#     for row in reader:
#         pan = row.get("pan")
#         cursor.execute("SELECT * FROM customers WHERE pan = %s", (pan,))
#         if cursor.fetchone():
#             skipped += 1
#             continue

#         cibil = generate_fixed_cibil(pan)
#         status = "Approved" if cibil >= 750 else "Rejected"
#         customer_id = str(uuid.uuid4())

#         cursor.execute("""
#         INSERT INTO customers (id, full_name, pan, dob, phone, loan_amount, cibil_score, status)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#         """, (
#             customer_id,
#             row.get('full_name'),
#             pan,
#             row.get('dob'),
#             row.get('phone'),
#             row.get('loan_amount'),
#             cibil,
#             status
#         ))
#         added += 1

#     db.commit()
#     return jsonify({"added": added, "skipped_duplicates": skipped})

# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)





# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import random

# app = Flask(__name__)
# CORS(app)  # Allow all origins, handles OPTIONS preflight automatically

# applications = []

# @app.route('/')
# def index():
#     return "Loan CRM backend is running!"

# @app.route('/apply', methods=['POST'])
# def apply():
#     data = request.json
#     print("Received data:", data)
    
#     full_name = data.get('full_name')
#     pan = data.get('pan')
#     dob = data.get('dob')
#     phone = data.get('phone')
#     loan_amount = data.get('loan_amount')

#     # Dummy logic for CIBIL Score
#     import random
#     cibil_score = random.randint(300, 900)
#     status = "Approved" if cibil_score >= 750 else "Rejected"

#     applications.append({
#         "full_name": full_name,
#         "pan": pan,
#         "dob": dob,
#         "phone": phone,
#         "loan_amount": loan_amount,
#         "cibil_score": cibil_score,
#         "status": status
#     })

#     return jsonify({
#         "status": status,
#         "cibil_score": cibil_score
#     })


# @app.route('/allApplications', methods=['GET'])
# def get_all():
#     return jsonify(applications)


# # ✅ Use Render-compatible port and host
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=10000)
    
    
    
    
    
    # app.run(host='0.0.0.0', port=port)


# from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS
# import random

# app = Flask(__name__)
# CORS(app)

# data_store = []

# # CIBIL score mock
# def mock_cibil_score(pan):
#     return random.randint(300, 900)

# # Decision logic
# def decide_status(score):
#     if score >= 750:
#         return "Approved"
#     elif score >= 600:
#         return "Pending"
#     else:
#         return "Rejected"

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/applyLoan', methods=['POST'])
# def apply_loan():
#     customer = request.get_json()

#     for entry in data_store:
#         if entry["pan"] == customer["pan"]:
#             return jsonify({"status": "Duplicate Entry", "message": "PAN already exists."})

#     score = mock_cibil_score(customer["pan"])
#     loan_status = decide_status(score)

#     customer["cibil_score"] = score
#     customer["status"] = loan_status
#     data_store.append(customer)
#     print("Data Store:", data_store)

#     return jsonify({
#         "message": "Loan application processed.",
#         "cibil_score": score,
#         "loan_status": loan_status
#     })

# @app.route('/allApplications', methods=['GET'])
# def get_all():
#     return jsonify(data_store)

# if __name__ == '__main__':
#     app.run(debug=True)




# from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS
# import random

# app = Flask(__name__)
# data_store = []

# # Mocked Surepass CIBIL API
# def mock_cibil_score(pan):
#     return random.randint(300, 900)

# # Loan decision logic
# def decide_status(score):
#     if score >= 750:
#         return "Approved"
#     elif score >= 600:
#         return "Pending"
#     else:
#         return "Rejected"

# @app.route('/applyLoan', methods=['POST'])
# def apply_loan():
#     customer = request.get_json()

#     # Duplicate check based on PAN
#     for entry in data_store:
#         if entry["pan"] == customer["pan"]:
#             return jsonify({"status": "Duplicate Entry", "message": "PAN already exists."})

#     # Get CIBIL score
#     score = mock_cibil_score(customer["pan"])
#     loan_status = decide_status(score)

#     customer["cibil_score"] = score
#     customer["status"] = loan_status
#     data_store.append(customer)
#     print("Current Data Store:", data_store)

#     return jsonify({
#         "message": "Loan application processed.",
#         "cibil_score": score,
#         "loan_status": loan_status
#     })
# # Route to view all submitted loan applications
# @app.route('/allApplications', methods=['GET'])
# def get_all():
#     return jsonify(data_store)


# if __name__ == '__main__':
#     app.run(debug=True)


