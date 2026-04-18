from fastapi import FastAPI, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from mongo_connection import get_database
from fetch_data import fetch_data_ai_workload
from fetch_data import fetch_data_ai_workload, fetch_ai_gpu_correlation
from kpi.kpi_service import (
    get_all_kpis,
    get_user_kpi,
    get_application_kpi,
    get_gpu_kpi,
    get_queue_kpi,
    get_gpu_token_trend_kpi,
    get_system_zones_kpi
    
)
from kpi.advance_kpi import compute_gpu_token_correlation
app = FastAPI()

COLLECTION_NAME = "your_collection"
MAX_RANGE_SECONDS = 3600  # 1 hour


# ✅ INDEX CREATED ONLY ONCE HERE
@app.on_event("startup")
def create_indexes():
    client, db = get_database()
    collection = db[COLLECTION_NAME]

    collection.create_index(
        [("node_id", 1), ("timestamp", -1)],
        name="node_timestamp_idx"
    )

    client.close()
    print("✅ Index ensured at startup")


# -----------------------------
# Validation
# -----------------------------
def validate_range(start_ts, end_ts):
    if start_ts and end_ts:
        start = datetime.fromisoformat(start_ts)
        end = datetime.fromisoformat(end_ts)

        if end < start:
            raise HTTPException(status_code=400, detail="end_ts must be after start_ts")

        if (end - start).total_seconds() > MAX_RANGE_SECONDS:
            raise HTTPException(
                status_code=400,
                detail="Time range too large (max 1 hour)"
            )


# -----------------------------
# API
# -----------------------------
@app.get("/ai-workload")
def get_ai_workload(
    node_id: str,
    start_ts: Optional[str] = Query(None),
    end_ts: Optional[str] = Query(None),
    last_seconds: Optional[int] = Query(None),
    limit: int = 100
):

    # 🔹 Recommended mode
    if last_seconds:
        if last_seconds > 3600:
            raise HTTPException(status_code=400, detail="Max last_seconds = 3600")

        end = datetime.utcnow()
        start = end - timedelta(seconds=last_seconds)

        return {
            "data": fetch_data_ai_workload(
                node_id=node_id,
                start_ts=start.isoformat(),
                end_ts=end.isoformat(),
                limit=limit
            )
        }

    # 🔹 Custom range
    if start_ts or end_ts:
        validate_range(start_ts, end_ts)

    return {
        "data": fetch_data_ai_workload(
            node_id=node_id,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=limit
        )
    }


@app.get("/ai-gpu-correlation")
def get_ai_gpu_correlation(
    node_id: str,
    start_ts: str = None,
    end_ts: str = None,
    last_seconds: int = None,
    limit: int = 50
):

    # Preferred mode
    if last_seconds:
        from datetime import datetime, timedelta

        end = datetime.utcnow()
        start = end - timedelta(seconds=last_seconds)

        return {
            "data": fetch_ai_gpu_correlation(
                node_id=node_id,
                start_ts=start.isoformat(),
                end_ts=end.isoformat(),
                limit=limit
            )
        }

    return {
        "data": fetch_ai_gpu_correlation(
            node_id=node_id,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=limit
        )
    }  
    
    
@app.post("/all-kpi")
def all_kpi(payload: dict):

    return get_all_kpis(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )
    
    
@app.post("/kpi/user")
def user_kpi(payload: dict):

    return get_user_kpi(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )
    
@app.post("/kpi/application")
def application_kpi(payload: dict):

    return get_application_kpi(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )
    
    
@app.post("/kpi/gpu")
def gpu_kpi(payload: dict):

    return get_gpu_kpi(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )


@app.post("/kpi/all")
def all_kpi(payload: dict):

    return get_all_kpis(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )
    
@app.get("/kpi/queue/realtime")
def queue_kpi_realtime(node_id: str, last_seconds: int = 60):

    from datetime import datetime, timedelta

    end = datetime.utcnow()
    start = end - timedelta(seconds=last_seconds)

    return get_queue_kpi([node_id], start.isoformat(), end.isoformat())

from kpi.advance_kpi import compute_gpu_token_correlation

@app.post("/kpi/gpu-token-trend")
def gpu_token_trend(payload: dict):

    return get_gpu_token_trend_kpi(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )
    
@app.get("/kpi/gpu-token-trend/realtime")
def gpu_token_trend_realtime(node_id: str, last_seconds: int = 60):

    from datetime import datetime, timedelta

    end = datetime.utcnow()
    start = end - timedelta(seconds=last_seconds)

    return get_gpu_token_trend_kpi(
        node_ids=[node_id],
        start_ts=start.isoformat(),
        end_ts=end.isoformat()
    )
    


@app.post("/kpi/gpu-token-trend-full")
def gpu_token_trend_full(payload: dict):

    trend = get_gpu_token_trend_kpi(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )

    return {
        "trend": trend,
        "correlation": compute_gpu_token_correlation(trend)
    }
    
    
@app.post("/kpi/system_zones")
def system_zones(payload: dict):

    return get_system_zones_kpi(
        node_ids=payload.get("node_ids"),
        start_ts=payload.get("start_time"),
        end_ts=payload.get("end_time")
    )
#/ai-workload?node_id=node-7cc255efed8e&last_seconds=60
#/ai-workload?node_id=node-7cc255efed8e&start_ts=2026-04-16T12:17:00+00:00&end_ts=2026-04-16T12:18:00+00:00