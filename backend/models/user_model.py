from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv
import re

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_default_database()
users = db.users

auth = Blueprint('auth', __name__)

# Email validation function
def is_valid_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

# Password strength validation
def is_strong_password(password):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit")
    if not any(char.isalpha() for char in password):
        raise ValueError("Password must contain at least one letter")
    return True

@auth.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not data.get('email') or not is_valid_email(data['email']):
            return jsonify({"error": "Invalid email address"}), 400
        if not data.get('password'):
            return jsonify({"error": "Password is required"}), 400
        if not is_strong_password(data['password']):
            return jsonify({"error": "Password is too weak"}), 400

        existing_user = users.find_one({"email": data["email"]})
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400

        hashed_password = generate_password_hash(data['password'])
        new_user = {
            "email": data["email"],
            "password": hashed_password,
            "name": data.get("name", ""),
            "score": 0,
            "activities": [],
            "emission": 0,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        users.insert_one(new_user)
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password are required"}), 400

        user = users.find_one({"email": data["email"]})
        if not user or not check_password_hash(user["password"], data["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        access_token = create_access_token(
            identity=str(user["_id"]),
            expires_delta=datetime.timedelta(days=7)
        )

        # Update last login
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.datetime.utcnow()}}
        )

        return jsonify({
            "token": access_token,
            "message": "Login successful",
            "user": {"email": user["email"]}
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
