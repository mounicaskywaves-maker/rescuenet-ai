import json
import os
curl -X POST YOUR_CLOUD_FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"sos_text": "Severe flooding near 16.5062, 80.6480. 3 people trapped on roof needing immediate rescue."}'
import functions_framework
from google import genai
from google.genai import types
from google.cloud import bigquery

ai_client = genai.Client()
bq_client = bigquery.Client()

DATASET_ID = "rescuenet"
TABLE_ID = "emergency_alerts"

# Active models array prioritizing gemini-3.6-flash
CANDIDATE_MODELS = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-2.5-pro']

def safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def safe_int(val, default=1):
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def safe_str(val, default="Unknown"):
    return str(val) if val is not None else default

@functions_framework.http
def handle_sos_webhook(request):
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    request_json = request.get_json(silent=True) or {}
    sos_text = request_json.get("sos_text", "")
           or request_json.get('message') 
        or request_json.get('text') 
    phone_number = request_json.get("phone", "Unknown")

    if not sos_text:
                return ({"error": "Missing input parameter. Provide 'sos_text', 'message', or 'text'."}, 400, headers)

    try:
        prompt = f"Extract disaster triage details from this SOS input: '{sos_text}'"
        
        response = None
        last_error = None

        for model_name in CANDIDATE_MODELS:
            try:
                response = ai_client.models.generate_content(

                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        system_instruction=(
                            "You are an emergency distress parser. Extract details accurately and output strictly valid JSON with keys: "
                            "disaster_type (string), severity_score (integer 1-5 where 5 is immediate life threat), "
                            "victim_count (integer), trapped_status (boolean), medical_urgency (boolean), "
                            "latitude (float), longitude (float), summary (string)."
                        )
                    )
                )
                if response and response.text:
                    break
            except Exception as model_err:
                last_error = model_err
                continue

        if not response or not response.text:
            raise Exception(f"All model attempts failed. Last error: {str(last_error)}")

        parsed_json = json.loads(response.text)

        disaster_type = safe_str(parsed_json.get("disaster_type"), "Emergency")
        severity = safe_int(parsed_json.get("severity_score"), 1)
        victims = safe_int(parsed_json.get("victim_count"), 1)
        trapped = bool(parsed_json.get("trapped_status", False))
        medical = bool(parsed_json.get("medical_urgency", False))
        lat = safe_float(parsed_json.get("latitude"), 0.0)
        lng = safe_float(parsed_json.get("longitude"), 0.0)
        summary = safe_str(parsed_json.get("summary"), "SOS alert received.")

        query = f"""
        INSERT INTO `{bq_client.project}.{DATASET_ID}.{TABLE_ID}` 
        (phone_number, disaster_type, severity_score, victim_count, trapped_status, medical_urgency, summary, latitude, longitude, location)
        VALUES (
            @phone, @disaster, @severity, @victims, @trapped, @medical, @summary, @lat, @lng,
            ST_GEOGPOINT(@lng, @lat)
        )
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("phone", "STRING", str(phone_number)),
                bigquery.ScalarQueryParameter("disaster", "STRING", disaster_type),
                bigquery.ScalarQueryParameter("severity", "INT64", severity),
                bigquery.ScalarQueryParameter("victims", "INT64", victims),
                bigquery.ScalarQueryParameter("trapped", "BOOL", trapped),
                bigquery.ScalarQueryParameter("medical", "BOOL", medical),
                bigquery.ScalarQueryParameter("summary", "STRING", summary),
                bigquery.ScalarQueryParameter("lat", "FLOAT64", lat),
                bigquery.ScalarQueryParameter("lng", "FLOAT64", lng),
            ]
        )

        query_job = bq_client.query(query, job_config=job_config)
        query_job.result()

        return (json.dumps({"status": "SUCCESS", "parsed_data": parsed_json}), 200, headers)

    except Exception as e:
        return (json.dumps({"status": "ERROR", "message": str(e)}), 500, headers)
