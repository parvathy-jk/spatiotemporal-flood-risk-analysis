from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MONGO_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "flood_risk_analysis"


def get_database():
    """Connect to MongoDB and return the project database."""
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    try:
        client.admin.command("ping")
        print("MongoDB connection successful!")
        return client, client[DATABASE_NAME]

    except ConnectionFailure:
        client.close()
        raise RuntimeError(
            "Could not connect to MongoDB. "
            "Check whether the MongoDB server is running."
        )