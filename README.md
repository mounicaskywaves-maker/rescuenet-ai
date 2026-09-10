Bash
# 🚨 RescuENet AI — Serverless Disaster Triage Pipeline

RescuENet AI is a real-time, serverless emergency distress processing system built for disaster response teams. It accepts unstructured SOS text messages from citizens, uses Google Gemini AI to extract critical triage metadata and spatial coordinates, and streams the data directly into BigQuery PostGIS for live mapping on Looker Studio.

---

## 🏗️ Architecture & Pipeline Overview

[ HTML Web SOS Portal ] │ (HTTP POST) ▼ [ GCP Cloud Functions Gen 2 (Python 3.11) ] │ ├─► [ Gemini API (gemini-3.6-flash) ] ── (Parses disaster type, severity, & coordinates) │ ▼ [ BigQuery GIS (rescuenet.emergency_alerts) ] ── (Executes ST_GEOGPOINT spatial insertion) │ ▼ [ Looker Studio Incident Dashboard ] ── (Live geographical pin rendering)
---

## 🛠️ GCP Tech Stack

* **Compute:** GCP Cloud Functions (2nd Gen, Python 3.11)
* **Artificial Intelligence:** Google GenAI SDK (`gemini-3.6-flash` with multi-model fallback to `gemini-2.5-flash` / `gemini-2.5-pro`)
* **Spatial Database:** Google BigQuery PostGIS (`GEOGRAPHY` column types, `ST_GEOGPOINT`)
* **Visualization:** Looker Studio (Real-time GIS geo-mapping)
* **Frontend:** Lightweight HTML5 / Vanilla JS SOS Dispatch Portal

---

## 📋 BigQuery Table Schema (`emergency_alerts`)

| Field Name | Type | Mode |
| :--- | :--- | :--- |
| `phone_number` | STRING | NULLABLE |
| `disaster_type` | STRING | NULLABLE |
| `severity_score` | INTEGER | NULLABLE |
| `victim_count` | INTEGER | NULLABLE |
| `trapped_status` | BOOLEAN | NULLABLE |
| `medical_urgency` | BOOLEAN | NULLABLE |
| `summary` | STRING | NULLABLE |
| `latitude` | FLOAT | NULLABLE |
| `longitude` | FLOAT | NULLABLE |
| `location` | GEOGRAPHY | NULLABLE |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

---

## 🚀 Deployment Instructions

### 1. Clone & Navigate
```bash
git clone [https://github.com/YOUR_USERNAME/rescuenet-ai.git](https://github.com/YOUR_USERNAME/rescuenet-ai.git)
cd rescuenet-ai
2. Set Up Environment & BigQuery
Bash

bq mk --dataset rescuenet
bq query --use_legacy_sql=false '
CREATE TABLE rescuenet.emergency_alerts (
    phone_number STRING,
    disaster_type STRING,
    severity_score INT64,
    victim_count INT64,
    trapped_status BOOL,
    medical_urgency BOOL,
    summary STRING,
    latitude FLOAT64,
    longitude FLOAT64,
    location GEOGRAPHY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);'
3. Deploy Cloud Function
Bash

gcloud functions deploy rescuenet-webhook \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=handle_sos_webhook \
  --trigger-http \
  --set-env-vars GEMINI_API_KEY="YOUR_GEMINI_API_KEY" \
  --allow-unauthenticated
EOF
---
