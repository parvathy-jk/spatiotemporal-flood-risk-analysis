from pymongo import MongoClient
from .config import MONGO_URI, DATABASE_NAME


def get_database():
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    # Verify the server is reachable.
    client.admin.command("ping")

    database = client[DATABASE_NAME]

    return client, database


if __name__ == "__main__":
    client = None

    try:
        client, database = get_database()

        print("MongoDB connection successful!")
        print("Database:", database.name)
        print("Existing collections:", database.list_collection_names())

    except Exception as error:
        print("MongoDB connection failed:", error)

    finally:
        if client is not None:
            client.close()