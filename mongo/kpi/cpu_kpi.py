def get_cpu_time_series_10s(db, match):

    pipeline = [
        {"$match": match},

        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$timestamp",
                        "unit": "second",
                        "binSize": 10
                    }
                },
                "avg_cpu": {"$avg": "$cpu_usage_percent"}
            }
        },

        {"$sort": {"_id": 1}},

        {
            "$project": {
                "_id": 0,
                "time": "$_id",
                "cpu_util": "$avg_cpu"
            }
        }
    ]

    return list(db["hardware_cpu"].aggregate(pipeline))