import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- CONFIGURATION ---
# Replace this with your actual API key string if the environment variable fails!
API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_ACTUAL_API_KEY_HERE")

if API_KEY == "YOUR_ACTUAL_API_KEY_HERE" or not API_KEY:
    print("❌ ERROR: Please set your GEMINI_API_KEY before running!")
    print("Run this in terminal first: export GEMINI_API_KEY='your_key'")
    exit(1)

# Pass the API key directly to the client
client = genai.Client(api_key=API_KEY)

class EmergencyDetails(BaseModel):
    location: str = Field(description="The physical location or landmarks mentioned.")
    victim_age: int = Field(description="The age of the victim, or -1 if unknown.")
    injury_level: int = Field(description="Severity level on a scale from 1 to 5.")
    immediate_needs: list[str] = Field(description="Resource needs like clean water, medical, or rescue.")

def process_emergency_data():
    sms_text = "Victim is around 45 years old at Sector 4 main street. Leg injury level 4. Needs immediate medical help and clean water."
    
    print("Processing with Gemini...")
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[
                sms_text,
                "Extract location, victim age, injury level 1-5, and immediate needs like clean water/medical/rescue."
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EmergencyDetails,
                temperature=0.1,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"\n❌ API Call Failed: {e}")
        return None

if __name__ == "__main__":
    result = process_emergency_data()
    if result:
        print("\n--- Final JSON Output ---")
        print(json.dumps(result, indent=2))
