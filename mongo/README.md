# 🚀 AI Workload Observability & KPI Service

A FastAPI-based backend for **AI workload monitoring, GPU/CPU observability, KPI analytics, and system diagnosis**.

---

# 🧠 What this system does

This service helps you:

* 📊 Track AI workload (requests, tokens, latency)
* ⚡ Monitor GPU & CPU utilization
* 🔗 Correlate workload with hardware usage
* 📈 Generate KPIs (user, application, infrastructure)
* 🔥 Build real-time trends (GPU vs tokens)
* 🧠 Detect system inefficiencies (CPU/GPU bottlenecks)

---

# 🏗️ Architecture

```text id="arch01"
AI Workload + Hardware Metrics → KPI Engine → Correlation → Diagnosis → API
```

---

# 📁 Project Structure

```text id="struct01"
mongo/
 ├── main.py
 ├── mongo_connection.py
 ├── fetch_data.py

 ├── kpi/
 │    ├── base.py
 │    ├── kpi_service.py
 │    ├── user_kpi.py
 │    ├── application_kpi.py
 │    ├── gpu_kpi.py
 │    ├── cpu_kpi.py
 │    ├── advance_kpi.py
```

---

# ⚙️ Setup

## Install dependencies

```bash id="setup01"
pip install fastapi uvicorn pymongo numpy
```

## Run server

```bash id="setup02"
uvicorn main:app --reload
```

---

# 🗄️ MongoDB Collections

* `ai_workload_real`
* `hardware_gpu`
* `hardware_cpu`

---

# 🚀 API Endpoints

---

## 📊 Core Workload APIs

### GET `/ai-workload`

Fetch AI workload data

**Params:**

* `node_id`
* `start_ts`, `end_ts`
* `last_seconds`
* `limit`

---

### GET `/ai-gpu-correlation`

Correlate AI workload with GPU usage

---

## 📈 KPI APIs

---

### POST `/kpi/all`

Returns complete KPI bundle

---

### POST `/kpi/user`

User-level metrics

---

### POST `/kpi/application`

Application/service metrics

---

### POST `/kpi/gpu`

GPU utilization & efficiency

---

## 🧮 Queue / Backlog KPI

### GET `/kpi/queue/realtime`

```bash id="queue01"
/kpi/queue/realtime?node_id=node-1&last_seconds=60
```

---

## 📊 Trend APIs

---

### POST `/kpi/gpu-token-trend`

GPU vs token trend

---

### GET `/kpi/gpu-token-trend/realtime`

Realtime trend

---

### POST `/kpi/gpu-token-trend-full`

Trend + correlation

---

## 🧠 System Diagnosis APIs

---

### POST `/kpi/system_zones`

Detect inefficiency zones

---

# 🧾 Example POST Request

```json id="req01"
{
  "node_ids": ["node-1"],
  "start_time": "2026-04-18T08:00:00",
  "end_time": "2026-04-18T08:05:00"
}
```

---

# 📊 Example Output

```json id="out01"
{
  "time": "2026-04-18T08:00:10",
  "tokens": 1500,
  "gpu_util": 35,
  "cpu_util": 85,
  "type": "cpu_bottleneck",
  "reason": "CPU is limiting GPU utilization"
}
```

---

# 🧠 Key Concepts

---

## 🔥 GPU Token Correlation

Measures how GPU usage scales with workload

| Value   | Meaning     |
| ------- | ----------- |
| > 0.8   | efficient   |
| 0.3–0.7 | moderate    |
| < 0.3   | inefficient |

---

## ⚡ Queue / Backlog KPI

```text id="concept01"
incoming_rps vs processing_rps
```

---

## 🧩 Inefficiency Zones

* cpu_bottleneck
* gpu_saturation
* pipeline_inefficiency
* gpu_waste

---

# 🚀 Features

* Modular KPI architecture
* Real-time analytics
* GPU + CPU correlation
* Trend analysis
* Bottleneck detection

---

# 🔮 Future Enhancements

* Alerting system
* Dashboard UI
* WebSocket streaming
* Recommendation engine
* Redis caching

---

# 🧠 Summary

```text id="summary01"
Workload → KPI → Correlation → Diagnosis
```

A complete backend for **AI observability & performance optimization**.

---
