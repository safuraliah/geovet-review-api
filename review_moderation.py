from flask import Flask, request, jsonify
from functools import wraps
import firebase_admin
from firebase_admin import credentials, firestore
import os, json
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load Firebase credentials from Render environment variable
cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
firebase_admin.initialize_app(cred)

db = firestore.client()

# Admin token from environment variable
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "ADMIN_TOKEN")

# Middleware to protect admin routes
def check_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if auth_header != f"Bearer {ADMIN_TOKEN}":
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def home():
    return jsonify({"message": "GeoVet Review API is live!"})

@app.route("/api/reviews/pending", methods=["GET"])
@check_admin
def get_pending_reviews():
    try:
        reviews = db.collection_group('reviews').where('status', '==', 'pending').stream()
        data = [{**r.to_dict(), "id": r.id} for r in reviews]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reviews/approve", methods=["POST"])
@check_admin
def approve_review():
    data = request.get_json()
    review_id = data.get("reviewId")

    if not review_id:
        return jsonify({"error": "Missing reviewId"}), 400

    try:
        found = False
        reviews = db.collection_group('reviews').where('status', '==', 'pending').stream()
        for review in reviews:
            if review.id == review_id:
                review.reference.update({"status": "approved"})
                found = True
                break
        if not found:
            return jsonify({"error": "Review not found"}), 404
        return jsonify({"message": "Review approved."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reviews/reject", methods=["POST"])
@check_admin
def reject_review():
    data = request.get_json()
    review_id = data.get("reviewId")

    if not review_id:
        return jsonify({"error": "Missing reviewId"}), 400

    try:
        found = False
        reviews = db.collection_group('reviews').where('status', '==', 'pending').stream()
        for review in reviews:
            if review.id == review_id:
                review.reference.delete()
                found = True
                break
        if not found:
            return jsonify({"error": "Review not found"}), 404
        return jsonify({"message": "Review rejected and deleted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
