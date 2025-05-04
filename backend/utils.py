from pymongo import MongoClient
from bson.objectid import ObjectId

def update_user_profile(user_id, update_data, mongo):
    """
    Update user profile based on provided user ID and update data.
    """
    try:
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0  # Returns True if the document was updated
    except Exception:
        return False
