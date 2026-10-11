from member3_analysis.mongodb.connection import get_database
from member3_analysis.mongodb.config import (
    RIVER_COLLECTION,
    RAINFALL_COLLECTION,
)


def district_water_level_summary(db):
    """Summarize river water levels by district."""
    return list(
        db[RIVER_COLLECTION].aggregate([
            {
                "$group": {
                    "_id": "$district",
                    "average_water_level": {
                        "$avg": "$average_water_level"
                    },
                    "maximum_water_level": {
                        "$max": "$maximum_water_level"
                    },
                    "total_observations": {"$sum": "$count"},
                    "stations": {"$addToSet": "$station"},
                }
            },
            {
                "$sort": {
                    "average_water_level": -1
                }
            },
        ])
    )


def station_water_level_summary(db):
    """Summarize water levels by station."""
    return list(
        db[RIVER_COLLECTION].aggregate([
            {
                "$group": {
                    "_id": "$station",
                    "district": {"$first": "$district"},
                    "average_water_level": {
                        "$avg": "$average_water_level"
                    },
                    "maximum_water_level": {
                        "$max": "$maximum_water_level"
                    },
                    "minimum_water_level": {
                        "$min": "$minimum_water_level"
                    },
                    "days_recorded": {"$sum": 1},
                }
            },
            {"$sort": {"maximum_water_level": -1}},
        ])
    )


def daily_rainfall_summary(db):
    """Calculate daily rainfall statistics."""
    return list(
        db[RAINFALL_COLLECTION].aggregate([
            {
                "$group": {
                    "_id": "$date",
                    "average_rainfall_mm": {"$avg": "$rainfall_mm"},
                    "maximum_rainfall_mm": {"$max": "$rainfall_mm"},
                    "minimum_rainfall_mm": {"$min": "$rainfall_mm"},
                    "grid_cells": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ])
    )


def highest_rainfall_cells(db, limit=10):
    """Find grid cells with the highest recorded rainfall."""
    return list(
        db[RAINFALL_COLLECTION].find(
            {},
            {
                "_id": 0,
                "grid_row": 1,
                "grid_col": 1,
                "date": 1,
                "latitude": 1,
                "longitude": 1,
                "rainfall_mm": 1,
            },
        ).sort("rainfall_mm", -1).limit(limit)
    )


def elevation_data_quality(db):
    """Summarize elevation data completeness."""
    return list(
        db[RAINFALL_COLLECTION].aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_records": {"$sum": 1},
                    "records_without_elevation": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$elevation_valid_pixels", 0]},
                                1,
                                0,
                            ]
                        }
                    },
                    "records_with_partial_elevation": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$gt": ["$elevation_valid_pixels", 0]},
                                        {"$gt": ["$elevation_missing_pixels", 0]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "records_with_complete_elevation": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$elevation_missing_pixels", 0]},
                                1,
                                0,
                            ]
                        }
                    },
                }
            }
        ])
    )


def main():
    client, db = get_database()

    try:
        print("\n--- DISTRICT WATER LEVEL SUMMARY ---")
        for item in district_water_level_summary(db):
            print(item)

        print("\n--- TOP 10 STATIONS BY MAXIMUM WATER LEVEL ---")
        for item in station_water_level_summary(db)[:10]:
            print(item)

        print("\n--- DAILY RAINFALL SUMMARY ---")
        for item in daily_rainfall_summary(db):
            print(item)

        print("\n--- TOP 10 RAINFALL GRID CELLS ---")
        for item in highest_rainfall_cells(db):
            print(item)

        print("\n--- ELEVATION DATA QUALITY ---")
        for item in elevation_data_quality(db):
            print(item)

    finally:
        client.close()


if __name__ == "__main__":
    main()