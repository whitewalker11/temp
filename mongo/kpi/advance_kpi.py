from datetime import datetime, timezone
import numpy as np


# -----------------------------
# ADVANCED KPI
# -----------------------------
def get_advanced_kpis(db, match):

    pipeline = [
        {"$match": match},

        # 🔥 convert timestamp
        {
            "$addFields": {
                "timestamp_dt": {"$toDate": "$timestamp"}
            }
        },

        {
            "$group": {
                "_id": None,

                "latencies": {"$push": "$processing_time_seconds"},
                "total_requests": {"$sum": 1},
                "total_tokens": {"$sum": "$total_tokens"},
                "total_cost": {"$sum": "$cost_usd"},

                # 🔥 FIXED
                "min_time": {"$min": "$timestamp_dt"},
                "max_time": {"$max": "$timestamp_dt"}
            }
        },

        {
            "$project": {
                "_id": 0,
                "total_requests": 1,
                "total_tokens": 1,
                "total_cost": 1,

                "avg_latency": {"$avg": "$latencies"},

                "p95_latency": {
                    "$arrayElemAt": [
                        {"$sortArray": {"input": "$latencies", "sortBy": 1}},
                        {
                            "$toInt": {
                                "$multiply": [0.95, {"$size": "$latencies"}]
                            }
                        }
                    ]
                },

                # 🔥 FIXED (datetime subtraction)
                "duration_sec": {
                    "$divide": [
                        {"$subtract": ["$max_time", "$min_time"]},
                        1000
                    ]
                }
            }
        },

        {
            "$project": {
                "total_requests": 1,
                "total_tokens": 1,
                "total_cost": 1,
                "avg_latency": 1,
                "p95_latency": 1,

                "requests_per_sec": {
                    "$cond": [
                        {"$gt": ["$duration_sec", 0]},
                        {"$divide": ["$total_requests", "$duration_sec"]},
                        0
                    ]
                },

                "tokens_per_sec": {
                    "$cond": [
                        {"$gt": ["$duration_sec", 0]},
                        {"$divide": ["$total_tokens", "$duration_sec"]},
                        0
                    ]
                },

                "cost_per_request": {
                    "$cond": [
                        {"$gt": ["$total_requests", 0]},
                        {"$divide": ["$total_cost", "$total_requests"]},
                        0
                    ]
                }
            }
        }
    ]

    res = list(db["ai_workload_real"].aggregate(pipeline))
    return res[0] if res else {}

def get_time_series(db, match):

    pipeline = [
        {"$match": match},

        {
            "$addFields": {
                "timestamp_dt": {"$toDate": "$timestamp"}
            }
        },

        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$timestamp_dt",
                        "unit": "minute"
                    }
                },
                "avg_latency": {"$avg": "$processing_time_seconds"},
                "requests": {"$sum": 1}
            }
        },

        {"$sort": {"_id": 1}},

        {
            "$project": {
                "time": "$_id",
                "avg_latency": 1,
                "requests": 1,
                "_id": 0
            }
        }
    ]

    return list(db["ai_workload_real"].aggregate(pipeline))


def get_time_series_10s(db, match):

    pipeline = [
        {"$match": match},

        {
            "$addFields": {
                "timestamp_dt": {"$toDate": "$timestamp"}
            }
        },

        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$timestamp_dt",
                        "unit": "second",
                        "binSize": 10
                    }
                },
                "tokens": {"$sum": "$total_tokens"},
                "requests": {"$sum": 1},
                "avg_latency": {"$avg": "$processing_time_seconds"}
            }
        },

        {"$sort": {"_id": 1}},

        {
            "$project": {
                "_id": 0,
                "time": "$_id",
                "tokens": 1,
                "requests": 1,
                "avg_latency": 1
            }
        }
    ]

    return list(db["ai_workload_real"].aggregate(pipeline))



def get_queue_backlog_kpi(db, match):

    pipeline = [
        {"$match": match},

        {
            "$addFields": {
                "timestamp_dt": {"$toDate": "$timestamp"}
            }
        },

        {
            "$group": {
                "_id": None,
                "total_requests": {"$sum": 1},
                "min_time": {"$min": "$timestamp_dt"},
                "max_time": {"$max": "$timestamp_dt"},
                "avg_latency": {"$avg": "$processing_time_seconds"}
            }
        },

        {
            "$project": {
                "_id": 0,
                "total_requests": 1,
                "avg_latency": 1,
                "duration_sec": {
                    "$divide": [
                        {"$subtract": ["$max_time", "$min_time"]},
                        1000
                    ]
                }
            }
        }
    ]

    res = list(db["ai_workload_real"].aggregate(pipeline))

    if not res:
        return {}

    r = res[0]

    duration = r.get("duration_sec", 1)
    total_requests = r.get("total_requests", 0)
    avg_latency = r.get("avg_latency", 0.001)

    incoming_rps = total_requests / duration if duration > 0 else 0
    processing_rps = 1 / avg_latency if avg_latency > 0 else 0

    backlog_growth = incoming_rps - processing_rps
    overloaded = incoming_rps > processing_rps

    return {
        "incoming_rps": round(incoming_rps, 2),
        "processing_rps": round(processing_rps, 2),
        "backlog_growth_rate": round(backlog_growth, 2),
        "overloaded": overloaded
    }
    
    
import numpy as np


def compute_gpu_token_correlation(data):

    tokens = [d["tokens"] for d in data]
    gpu = [d["gpu_util"] for d in data]

    if len(tokens) < 2:
        return {
            "value": 0,
            "interpretation": "Insufficient data",
            "insight": "Not enough data points to compute correlation",
            "possible_issue": "Increase time range"
        }

    corr = float(np.corrcoef(tokens, gpu)[0, 1])

    # ---------------- INTERPRETATION ----------------
    if corr >= 0.8:
        interpretation = "Very strong positive correlation"
        insight = "GPU utilization scales very well with workload"
        issue = None

    elif corr >= 0.6:
        interpretation = "Strong positive correlation"
        insight = "System is efficiently using GPU resources"
        issue = None

    elif corr >= 0.3:
        interpretation = "Moderate correlation"
        insight = "GPU usage partially reflects workload"
        issue = "Possible inefficiencies in batching or scheduling"

    elif corr >= 0:
        interpretation = "Weak correlation"
        insight = "GPU is not scaling properly with token load"
        issue = "Potential CPU bottleneck, IO delays, or suboptimal batching"

    else:
        interpretation = "Negative correlation"
        insight = "GPU usage decreases as workload increases (unexpected)"
        issue = "Possible misconfiguration, incorrect mapping, or resource contention"

    return {
        "value": round(corr, 3),
        "interpretation": interpretation,
        "insight": insight,
        "possible_issue": issue
    }
    

    
def detect_system_inefficiency_zones(trend):

    zones = []

    for row in trend:
        tokens = row.get("tokens", 0)
        gpu = row.get("gpu_util", 0)
        cpu = row.get("cpu_util", 0)

        zone = None

        # ---------------- CPU BOTTLENECK ----------------
        if tokens > 1000 and gpu < 40 and cpu > 70:
            zone = {
                "type": "cpu_bottleneck",
                "reason": "High workload but GPU underutilized while CPU is high"
            }

        # ---------------- GPU SATURATION ----------------
        elif gpu > 90 and tokens > 1000:
            zone = {
                "type": "gpu_saturation",
                "reason": "GPU is near max capacity under high load"
            }

        # ---------------- UNDERUTILIZATION ----------------
        elif tokens > 1000 and gpu < 40 and cpu < 50:
            zone = {
                "type": "pipeline_inefficiency",
                "reason": "Both CPU and GPU are underutilized despite high workload"
            }

        # ---------------- GPU WASTE ----------------
        elif gpu > 70 and tokens < 300:
            zone = {
                "type": "gpu_waste",
                "reason": "High GPU usage but low workload"
            }

        if zone:
            zones.append({
                "time": row["time"],
                "tokens": tokens,
                "gpu_util": gpu,
                "cpu_util": cpu,
                **zone
            })

    return zones