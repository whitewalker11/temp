from mongo_connection import get_database
from kpi.base import build_match

from kpi.user_kpi import get_user_summary
from kpi.application_kpi import get_application_details
from kpi.gpu_kpi import (
    get_gpu_summary,
    get_gpu_efficiency,
    get_gpu_time_series_10s
)
from kpi.top_kpi import get_top_users
from kpi.cpu_kpi import get_cpu_time_series_10s
from kpi.advance_kpi import (
    get_advanced_kpis,
    get_time_series,
    get_time_series_10s,
    compute_gpu_token_correlation,
    get_queue_backlog_kpi,
    detect_system_inefficiency_zones
)



# ---------------------------------------------------
# 🔥 MAIN KPI (ALL)
# ---------------------------------------------------
def get_all_kpis(node_ids, start_ts, end_ts):

    client, db = get_database()
    match = build_match(node_ids, start_ts, end_ts)

    response = {
        "filters": {
            "node_ids": node_ids,
            "start_time": start_ts,
            "end_time": end_ts
        },

        # ---------------- USER KPI ----------------
        "user_kpi": {
            "summary": get_user_summary(db, match),
            "top_3_users_by_tokens": get_top_users(db, match)
        },

        # ---------------- APPLICATION KPI ----------------
        "application_kpi": {
            "application_details": get_application_details(db, match)
        },

        # ---------------- GPU KPI ----------------
        "gpu_kpi": {
            "per_gpu": get_gpu_summary(db, match),
            "efficiency": get_gpu_efficiency(db, match)
        },

        # ---------------- ADVANCED KPI ----------------
        "advanced_kpi": get_advanced_kpis(db, match),

        # ---------------- BASIC TIME SERIES ----------------
        "time_series": get_time_series(db, match)
    }

    # ---------------------------------------------------
    # 🔥 GPU vs TOKEN TREND (10s bucket)
    # ---------------------------------------------------
    trend = get_gpu_vs_token_trend(db, match)
    zones = detect_system_inefficiency_zones(trend)

    response["gpu_vs_token_trend"] = trend
    response["system_load"] = get_queue_backlog_kpi(db, match)
    response["gpu_inefficiency_zones"] = zones

    # ---------------------------------------------------
    # 🔥 CORRELATION KPI
    # ---------------------------------------------------
    response["gpu_token_correlation"] = compute_gpu_token_correlation(trend)

    client.close()
    return response


# ---------------------------------------------------
# 🔥 INDIVIDUAL KPI APIs
# ---------------------------------------------------
def get_user_kpi(node_ids, start_ts, end_ts):
    client, db = get_database()
    match = build_match(node_ids, start_ts, end_ts)

    res = {
        "summary": get_user_summary(db, match),
        "top_3_users_by_tokens": get_top_users(db, match)
    }

    client.close()
    return res


def get_application_kpi(node_ids, start_ts, end_ts):
    client, db = get_database()
    match = build_match(node_ids, start_ts, end_ts)

    res = {
        "application_details": get_application_details(db, match)
    }

    client.close()
    return res


def get_gpu_kpi(node_ids, start_ts, end_ts):
    client, db = get_database()
    match = build_match(node_ids, start_ts, end_ts)

    res = {
        "per_gpu": get_gpu_summary(db, match),
        "efficiency": get_gpu_efficiency(db, match)
    }

    client.close()
    return res


# ---------------------------------------------------
# 🔥 GPU vs TOKEN TREND MERGE
# ---------------------------------------------------
def get_gpu_vs_token_trend(db, match):

    ai_data = get_time_series_10s(db, match)
    gpu_data = get_gpu_time_series_10s(db, match)
    cpu_data = get_cpu_time_series_10s(db, match)

    gpu_map = {str(d["time"]): d["gpu_util"] for d in gpu_data}
    cpu_map = {str(d["time"]): d["cpu_util"] for d in cpu_data}

    merged = []

    for row in ai_data:
        t = str(row["time"])

        merged.append({
            "time": row["time"],
            "tokens": row["tokens"],
            "requests": row["requests"],
            "gpu_util": gpu_map.get(t, 0),
            "cpu_util": cpu_map.get(t, 0)   # 🔥 NEW
        })

    return merged


def get_queue_kpi(node_ids, start_ts, end_ts):


    client, db = get_database()
    match = build_match(node_ids, start_ts, end_ts)

    res = get_queue_backlog_kpi(db, match)

    client.close()
    return res

def get_gpu_token_trend_kpi(node_ids, start_ts, end_ts):

    client, db = get_database()
    match = build_match(node_ids, start_ts, end_ts)

    trend = get_gpu_vs_token_trend(db, match)

    client.close()
    return trend

def get_system_zones_kpi(node_ids, start_ts, end_ts):

    client, db = get_database()
    match = build_match(node_ids, start_ts, end_ts)

    trend = get_gpu_vs_token_trend(db, match)

    zones = detect_system_inefficiency_zones(trend)


    client.close()
    return zones