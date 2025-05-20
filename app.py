from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins, handles OPTIONS preflight automatically

applications = []

@app.route('/apply', methods=['POST'])
def apply():
    data = request.json
    print("Received data:", data)
    
    full_name = data.get('full_name')
    pan = data.get('pan')
    dob = data.get('dob')
    phone = data.get('phone')
    loan_amount = data.get('loan_amount')

    # Dummy logic for CIBIL Score
    import random
    cibil_score = random.randint(300, 900)
    status = "Approved" if cibil_score >= 750 else "Rejected"

    applications.append({
        "full_name": full_name,
        "pan": pan,
        "dob": dob,
        "phone": phone,
        "loan_amount": loan_amount,
        "cibil_score": cibil_score,
        "status": status
    })

    return jsonify({
        "status": status,
        "cibil_score": cibil_score
    })


@app.route('/allApplications', methods=['GET'])
def get_all():
    return jsonify(applications)


if __name__ == '__main__':
    app.run(debug=True)


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


