def get_application_details(db, match):

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$service_name",
                "users": {"$addToSet": "$user_id"},
                "total_requests": {"$sum": 1},
                "total_tokens": {"$sum": "$total_tokens"},
                "avg_latency": {"$avg": "$processing_time_seconds"}
            }
        },
        {
            "$project": {
                "application": "$_id",
                "unique_users": {"$size": "$users"},
                "total_requests": 1,
                "total_tokens": 1,
                "avg_processing_time_sec": "$avg_latency"
            }
        }
    ]

    return list(db["ai_workload_real"].aggregate(pipeline))