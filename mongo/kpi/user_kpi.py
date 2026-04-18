def get_user_summary(db, match):

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$user_id",
                "total_requests": {"$sum": 1}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_unique_users": {"$sum": 1},
                "total_requests": {"$sum": "$total_requests"},
                "avg_requests_per_user": {"$avg": "$total_requests"}
            }
        }
    ]

    res = list(db["ai_workload_real"].aggregate(pipeline))
    return res[0] if res else {}