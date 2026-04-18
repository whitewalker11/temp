def get_gpu_summary(db, match):

    pipeline = [
        {"$match": match},
        {"$unwind": "$gpus"},
        {
            "$group": {
                "_id": "$gpus.index",
                "avg_util": {"$avg": "$gpus.utilization.gpu_pct"},
                "avg_memory": {"$avg": "$gpus.memory.used_mb"}
            }
        }
    ]

    return list(db["hardware_gpu"].aggregate(pipeline))


def get_gpu_efficiency(db, match):

    pipeline = [
        {"$match": match},

        {"$unwind": "$gpus"},

        {
            "$group": {
                "_id": None,
                "avg_gpu_util": {"$avg": "$gpus.utilization.gpu_pct"},
                "avg_gpu_mem": {"$avg": "$gpus.memory.used_mb"}
            }
        }
    ]

    res = list(db["hardware_gpu"].aggregate(pipeline))

    if not res:
        return {}

    r = res[0]

    return {
        "avg_gpu_utilization": r.get("avg_gpu_util", 0),
        "avg_gpu_memory_mb": r.get("avg_gpu_mem", 0),

        # efficiency heuristic
        "gpu_efficiency_score": (
            r.get("avg_gpu_util", 0) / 100
        )
    }
    
    
def get_gpu_time_series_10s(db, match):

    pipeline = [
        {"$match": match},
        {"$unwind": "$gpus"},

        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$timestamp",
                        "unit": "second",
                        "binSize": 10
                    }
                },
                "avg_gpu_util": {"$avg": "$gpus.utilization.gpu_pct"}
            }
        },

        {"$sort": {"_id": 1}},

        {
            "$project": {
                "_id": 0,
                "time": "$_id",
                "gpu_util": "$avg_gpu_util"
            }
        }
    ]

    return list(db["hardware_gpu"].aggregate(pipeline))