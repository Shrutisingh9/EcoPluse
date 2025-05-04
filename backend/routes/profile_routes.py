from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from profile_utils import update_user_profile
from db import mongo

profile = Blueprint('profile', __name__)

# Profile Update Endpoint
@profile.route('/update', methods=['PUT'])
@jwt_required()  # Ensure user is logged in
def update_profile():
    try:
        user_id = get_jwt_identity()  # Get user ID from JWT token

        # Get data to update
        update_data = request.json
        valid_fields = ['name', 'email', 'phone', 'country', 'occupation', 'gender', 'bio', 'location', 'profile_pic']

        # Filter only valid fields to update
        filtered_data = {key: update_data[key] for key in valid_fields if key in update_data}

        # Call function to update user profile
        is_updated = update_user_profile(user_id, filtered_data, mongo)

        if is_updated:
            return jsonify({"message": "Profile updated successfully!"}), 200
        else:
            return jsonify({"error": "Failed to update profile!"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
