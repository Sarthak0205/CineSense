from flask_pymongo import PyMongo

mongo = PyMongo()

def init_db(app):
    app.config["MONGO_URI"] = app.config.get("MONGO_URI") or "mongodb://localhost:27017/cineSenseDB"
    mongo.init_app(app)
