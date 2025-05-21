from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import mysql.connector
import os

app = Flask(__name__)
CORS(app)

# MySQL Connection
db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "loan_crm")
)
cursor = db.cursor(dictionary=True)

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(20),
    full_name VARCHAR(100),
    pan VARCHAR(20),
    dob VARCHAR(20),
    phone VARCHAR(15),
    loan_amount FLOAT,
    cibil_score INT,
    status VARCHAR(20)
)
""")
db.commit()

def generate_cibil_score(pan, dob):
    key = pan.strip().upper() + dob.strip()
    hashed = hashlib.sha256(key.encode()).hexdigest()
    numeric = int(hashed[:8], 16)
    return 300 + (numeric % 601)  # Range 300–900

def generate_customer_id(pan, dob):
    short = hashlib.md5((pan + dob).encode()).hexdigest()[:6]
    return f"CUST{short.upper()}"

@app.route('/apply', methods=['POST'])
def apply():
    data = request.json
    full_name = data.get('full_name')
    pan = data.get('pan')
    dob = data.get('dob')
    phone = data.get('phone')
    loan_amount = float(data.get('loan_amount'))

    cibil_score = generate_cibil_score(pan, dob)
    customer_id = generate_customer_id(pan, dob)
    status = "Approved" if cibil_score >= 750 else "Rejected"

    # Insert into DB (prevent duplicate PAN + DOB)
    cursor.execute("""
        SELECT * FROM applications WHERE pan=%s AND dob=%s
    """, (pan, dob))
    existing = cursor.fetchone()
    if existing:
        return jsonify({"message": "Duplicate application", "status": existing["status"], "cibil_score": existing["cibil_score"]})

    cursor.execute("""
        INSERT INTO applications (customer_id, full_name, pan, dob, phone, loan_amount, cibil_score, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (customer_id, full_name, pan, dob, phone, loan_amount, cibil_score, status))
    db.commit()

    return jsonify({
        "customer_id": customer_id,
        "status": status,
        "cibil_score": cibil_score
    })

@app.route('/allApplications', methods=['GET'])
def get_all():
    cursor.execute("SELECT * FROM applications")
    results = cursor.fetchall()
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




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


