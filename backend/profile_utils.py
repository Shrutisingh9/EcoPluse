from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_default_database()
users = db.users

def create_user(data):
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    hashed_pw = generate_password_hash(data['password'])
    user = {
        "name": data['name'],
        "email": data['email'],
        "password": hashed_pw,
        "phone": data.get('phone', ''),
        "country": data.get('country', ''),
        "occupation": data.get('occupation', ''),
        "gender": data.get('gender', ''),
        "location": data.get('location', ''),
        "profile_pic": data.get('profile_pic', ''),
        "score": 0,
        "activities": [],
        "emission": 0,
        "createdAt": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }
    users.insert_one(user)

def find_user_by_email(email):
    return users.find_one({"email": email})

def validate_password(input_password, stored_password_hash):
    return check_password_hash(stored_password_hash, input_password)

def get_user_by_id(user_id):
    try:
        user = users.find_one({'_id': ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
        return user
    except Exception:
        return None

def update_user_profile(user_id, update_data):
    try:
        update_data['updated_at'] = datetime.datetime.utcnow()  # Add timestamp
        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except Exception:
        return False
