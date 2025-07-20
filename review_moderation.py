from flask import Flask, request, jsonify
from functools import wraps
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load the admin token from .env
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# Initialize Firebase Admin SDK
firebase_credentials = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

# Admin authentication middleware
def check_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or auth != f"Bearer {ADMIN_TOKEN}":
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ✅ Get all pending reviews
@app.route('/api/reviews/pending', methods=['GET'])
@check_admin
def get_pending_reviews():
    try:
        reviews_ref = db.collection('reviews').where('status', '==', 'pending')
        reviews = reviews_ref.stream()
        result = [{**r.to_dict(), "id": r.id} for r in reviews]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Approve a review
@app.route('/api/reviews/approve', methods=['POST'])
@check_admin
def approve_review():
    data = request.get_json()
    review_id = data.get("reviewId")
    try:
        db.collection('reviews').document(review_id).update({"status": "approved"})
        return jsonify({"message": "Review approved."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Reject a review
@app.route('/api/reviews/reject', methods=['POST'])
@check_admin
def reject_review():
    data = request.get_json()
    review_id = data.get("reviewId")
    try:
        db.collection('reviews').document(review_id).delete()
        return jsonify({"message": "Review rejected and deleted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Run the app
if __name__ == '__main__':
    app.run(debug=True)
