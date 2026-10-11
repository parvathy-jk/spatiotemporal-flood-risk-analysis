import os

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017/"
)

DATABASE_NAME = os.getenv(
    "MONGO_DATABASE",
    "flood_risk_analysis"
)