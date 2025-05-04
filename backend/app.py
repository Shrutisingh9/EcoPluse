import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/ecopulse")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwtsecret")

# Initialize extensions
CORS(app)
mongo = PyMongo(app)
jwt = JWTManager(app)

# ------------------ AUTH ROUTES ------------------

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    if mongo.db.users.find_one({"email": data["email"]}):
        return jsonify({"success": False, "message": "Email already registered"}), 409

    hashed_pw = generate_password_hash(data["password"])
    mongo.db.users.insert_one({
        "email": data["email"],
        "password": hashed_pw,
        "name": data.get("name", ""),
        "score": 0,
        "activities": [],
        "emission": 0
    })

    return jsonify({"success": True, "message": "Registration successful"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    user = mongo.db.users.find_one({"email": data["email"]})
    if user and check_password_hash(user["password"], data["password"]):
        access_token = create_access_token(identity=user["email"])
        session["email"] = user["email"]  # Optional: for session fallback
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return jsonify({"success": True, "token": access_token, "user": user}), 200

    return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out"}), 200


@app.route("/api/user", methods=["GET"])
@jwt_required(optional=True)
def get_user():
    email = get_jwt_identity() or session.get("email")
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    user = mongo.db.users.find_one({"email": email}, {"password": 0})
    if user:
        user["_id"] = str(user["_id"])
        return jsonify(user), 200

    return jsonify({"error": "User not found"}), 404


# ------------------ CO2 CALCULATION ROUTES ------------------

def save_co2_data(user_email, data, co2_emission):
    try:
        record = {
            **data,
            "user_id": user_email,
            "co2_emission": co2_emission,
            "timestamp": datetime.utcnow()
        }
        mongo.db.co2_data.insert_one(record)
        return True
    except Exception as e:
        logging.error(f"Database error: {e}")
        return False


@app.route('/api/calculate_co2', methods=['POST'])
@jwt_required()
def calculate_co2():
    try:
        user_email = get_jwt_identity()
        req = request.json

        data = {
            "vehicle_type": req.get('vehicleType', '').lower(),
            "fuel_type": req.get('fuelType', '').lower(),
            "avg_km_per_week": float(req.get('avgKmPerWeek', 0)),
            "public_transport": req.get('publicTransportUsage', 'no').lower() == 'yes',
            "electricity": float(req.get('electricity', 0)),
            "gas_type": req.get('gasType', '').lower(),
            "gas_usage": float(req.get('gasUsage', 0)),
            "diet_type": req.get('dietType', '').lower(),
            "meals_per_day": float(req.get('mealsPerDay', 0)),
            "water_usage": float(req.get('waterUsage', 0)),
            "household_size": int(req.get('householdSize', 1)),
            "ac_usage": float(req.get('acUsage', 0)),
            "heater_usage": float(req.get('heaterUsage', 0)),
            "washing_frequency": float(req.get('washingFrequency', 0)),
            "online_orders": float(req.get('onlineOrders', 0)),
            "fast_delivery": req.get('fastDelivery', 'no').lower() == 'yes',
            "greenery_at_home": req.get('greeneryAtHome', 'no').lower() == 'yes'
        }

        # Validate values
        for key, value in data.items():
            if isinstance(value, (int, float)) and value < 0:
                return jsonify({'error': f'{key} cannot be negative'}), 400

        # Emission calculation
        fuel_factor = {
            'petrol': 2.31,
            'diesel': 2.68,
            'electric': 0.5,
            'cng': 1.6
        }.get(data["fuel_type"], 2.0)

        vehicle_emission = data["avg_km_per_week"] * fuel_factor * 0.1
        if data["public_transport"]:
            vehicle_emission *= 0.7

        electricity_emission = data["electricity"] * 0.5
        gas_emission = data["gas_usage"] * 0.3

        diet_factors = {
            'vegan': 1.5,
            'vegetarian': 2.0,
            'non-vegetarian': 3.5
        }
        diet_emission = data["meals_per_day"] * diet_factors.get(data["diet_type"], 2.5) * 30

        water_emission = data["water_usage"] * data["household_size"] * 0.01

        appliance_emission = (
            data["ac_usage"] * 0.15 * 30 +
            data["heater_usage"] * 0.2 * 30 +
            data["washing_frequency"] * 0.4 * 4
        )

        delivery_emission = data["online_orders"] * 0.6
        if data["fast_delivery"]:
            delivery_emission *= 1.5

        greenery_offset = 2.0 if data["greenery_at_home"] else 0

        total_co2 = vehicle_emission + electricity_emission + gas_emission + diet_emission + \
                    water_emission + appliance_emission + delivery_emission - greenery_offset

        badge = "Eco Hero" if total_co2 < 200 else "Eco Aware" if total_co2 < 400 else "Needs Improvement"

        if not save_co2_data(user_email, data, total_co2):
            return jsonify({'error': 'Failed to save CO₂ data'}), 500

        return jsonify({
            'co2_emission': round(total_co2, 2),
            'badge': badge,
            'message': f'Estimated CO₂ Emission: {total_co2:.2f} kg/month',
            'input_data': data
        }), 200

    except Exception as e:
        logging.error(f"Calculation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user_co2_data', methods=['GET'])
@jwt_required()
def get_user_co2_data():
    try:
        user_email = get_jwt_identity()
        data = list(mongo.db.co2_data.find({'user_id': user_email}))
        for d in data:
            d['_id'] = str(d['_id'])
            d['timestamp'] = d['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(data), 200
    except Exception as e:
        logging.error(f"Data fetch error: {e}")
        return jsonify({'error': str(e)}), 500


# ------------------ RUN SERVER ------------------

if __name__ == '__main__':
    try:
        mongo.cx.admin.command("ping")
        print("✅ MongoDB connected successfully!")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)

    app.run(debug=True, port=5000, use_reloader=False)
