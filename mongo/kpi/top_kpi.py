def get_top_users(db, match):

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$user_id",
                "total_tokens": {"$sum": "$total_tokens"},
                "total_requests": {"$sum": 1}
            }
        },
        {"$sort": {"total_tokens": -1}},
        {"$limit": 3}
    ]

    return list(db["ai_workload_real"].aggregate(pipeline))