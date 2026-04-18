from datetime import datetime
from mongo_connection import get_database

COLLECTION_NAME = "your_collection"


def parse_iso(ts_str):
    return datetime.fromisoformat(ts_str)


def fetch_data_ai_workload(node_id, start_ts=None, end_ts=None, limit=100):

    client, db = get_database()
    collection = db[COLLECTION_NAME]

    query = {"node_id": node_id}

    # Timestamp filter
    if start_ts or end_ts:
        time_filter = {}

        if start_ts:
            time_filter["$gte"] = parse_iso(start_ts)

        if end_ts:
            time_filter["$lte"] = parse_iso(end_ts)

        query["timestamp"] = time_filter

    cursor = collection.find(
        query,
        {
            "_id": 0,
            "request_id": 1,
            "node_id": 1,
            "pid": 1,
            "service_name": 1,
            "model_name": 1,
            "gpu_vendor": 1,
            "processing_time_seconds": 1,
            "total_time_seconds": 1,
            "tokens_per_second": 1,
            "cost_usd": 1,
            "timestamp": 1
        }
    ).sort("timestamp", -1).limit(limit)

    results = list(cursor)

    client.close()
    return results

from datetime import datetime, timedelta
from mongo_connection import get_database


def fetch_ai_gpu_correlation(node_id, start_ts=None, end_ts=None, limit=50):

    client, db = get_database()

    ai_collection = db["ai_workload_real"]

    # Convert timestamps
    def parse(ts):
        return datetime.fromisoformat(ts) if ts else None

    start_time = parse(start_ts)
    end_time = parse(end_ts)

    pipeline = [
        {
            "$match": {
                "node_id": node_id,
                **(
                    {
                        "timestamp": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                    if start_time and end_time else {}
                )
            }
        },
        {"$sort": {"timestamp": -1}},
        {"$limit": limit},

        # 🔥 Lookup GPU doc (time-window based)
        {
            "$lookup": {
                "from": "hardware_gpu",
                "let": {
                    "pid": "$pid",
                    "node": "$node_id",
                    "ts": "$timestamp"
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$node_id", "$$node"]},
                                    {
                                        "$gte": [
                                            "$timestamp",
                                            {"$subtract": ["$$ts", 2000]}  # -2 sec
                                        ]
                                    },
                                    {
                                        "$lte": [
                                            "$timestamp",
                                            {"$add": ["$$ts", 2000]}  # +2 sec
                                        ]
                                    }
                                ]
                            }
                        }
                    },
                    {"$limit": 1}
                ],
                "as": "gpu_doc"
            }
        },

        {"$unwind": {"path": "$gpu_doc", "preserveNullAndEmptyArrays": True}},

        # 🔥 Extract matching process by PID
        {
            "$addFields": {
                "matched_process": {
                    "$filter": {
                        "input": "$gpu_doc.processes",
                        "as": "proc",
                        "cond": {"$eq": ["$$proc.pid", "$pid"]}
                    }
                }
            }
        },

        {"$unwind": {"path": "$matched_process", "preserveNullAndEmptyArrays": True}},

        # 🔥 Final projection
        {
            "$project": {
                "_id": 0,
                "request_id": 1,
                "node_id": 1,
                "pid": 1,
                "model_name": 1,
                "processing_time_seconds": 1,
                "tokens_per_second": 1,
                "timestamp": 1,

                # GPU fields
                "gpu_index": "$matched_process.gpu_index",
                "gpu_mem_mb": "$matched_process.gpu_mem_mb",
                "sm_pct": "$matched_process.sm_pct",
                "cpu_pct": "$matched_process.cpu_pct",
                "cmdline": "$matched_process.cmdline"
            }
        }
    ]

    result = list(ai_collection.aggregate(pipeline))

    client.close()
    return result


from datetime import datetime


def _parse(ts):
    return datetime.fromisoformat(ts) if ts else None


def _base_match(node_ids, start_ts, end_ts):
    match = {}

    if node_ids:
        match["node_id"] = {"$in": node_ids}

    if start_ts and end_ts:
        match["timestamp"] = {
            "$gte": _parse(start_ts),
            "$lte": _parse(end_ts)
        }

    return match