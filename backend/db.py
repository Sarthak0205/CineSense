from pymongo import MongoClient
from config import Config

def init_db(app):
    client = MongoClient(Config.MONGO_URI)
    db = client[Config.DB_NAME]
    app.db = db
    
    # Create indexes
    db.users.create_index('email', unique=True)
    db.favorites.create_index([('user_id', 1), ('movie_id', 1)], unique=True)
    
    print(f"✅ Connected to MongoDB: {Config.DB_NAME}")
    return db