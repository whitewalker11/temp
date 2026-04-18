from datetime import datetime


def parse_ts(ts):
    return datetime.fromisoformat(ts) if ts else None


def build_match(node_ids, start_ts, end_ts):
    match = {}

    if node_ids:
        match["node_id"] = {"$in": node_ids}

    if start_ts and end_ts:
        match["timestamp"] = {
            "$gte": parse_ts(start_ts),
            "$lte": parse_ts(end_ts)
        }

    return match