from datetime import datetime, timezone


def parse_iso(ts):
    dt = datetime.fromisoformat(ts)

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)

    return dt.isoformat()   # 🔥 STRING


def build_match(node_ids, start_ts, end_ts):
    return {
        "node_id": {"$in": node_ids},
        "timestamp": {
            "$gte": parse_iso(start_ts),
            "$lte": parse_iso(end_ts)
        }
    }