import os
import time
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/triage"

def test_split_api_flow():
    print("--- 🧪 Testing MedGemma Split-API Flow ---")
    
    # Path to a dummy audio file
    audio_file = "storage/audio/b0050b51-e733-489f-9c9b-082beef88b63_triage_1772519875995.webm"
    if not os.path.exists(audio_file):
        # List files in storage/audio to find a substitute
        audio_dir = "storage/audio"
        files = [f for f in os.listdir(audio_dir) if f.endswith(".webm")]
        if files:
            audio_file = os.path.join(audio_dir, files[0])
            print(f"💡 Using alternative audio: {audio_file}")
        else:
            print(f"❌ No audio files found in {audio_dir}")
            return

    # STAGE 1: POST /triage/vitals
    vitals_data = {
        "patient_id": "P-TEST-SPLIT",
        "language": "English",
        "patient_age": 45,
        "temp": 39.8,        # ABNORMAL
        "bp_sys": 175,      # ABNORMAL
        "bp_dia": 105,
        "hr": 130,          # ABNORMAL
        "spo2": 89          # ABNORMAL
    }

    print(f"\n📡 STAGE 1: Sending Vitals (Abnormal Task)...")
    start_vitals = time.time()
    try:
        v_resp = requests.post(f"{BASE_URL}/vitals", data=vitals_data)
        v_latency = time.time() - start_vitals
        
        if v_resp.status_code == 200:
            result = v_resp.json()
            triage_id = result.get("id")
            print(f"✅ Vitals Success in {v_latency:.2f}s")
            print(f"Triage ID: {triage_id}")
            print(f"Status: {result.get('vitals_status')}")
            print(f"Precautions: {result.get('preliminary_precautions')}")
            
            if not triage_id:
                print("❌ FAIL: No Triage ID returned.")
                return

            # STAGE 2: POST /triage/audio/{id}
            print(f"\n📡 STAGE 2: Uploading Audio for Triage {triage_id}...")
            start_audio = time.time()
            
            files = {
                "audio": (os.path.basename(audio_file), open(audio_file, "rb"), "audio/webm")
            }
            audio_data = {"language": "English"}
            
            a_resp = requests.post(f"{BASE_URL}/audio/{triage_id}", files=files, data=audio_data)
            a_latency = time.time() - start_audio
            
            if a_resp.status_code == 200:
                print(f"✅ Audio Upload Success in {a_latency:.2f}s")
                print(f"Status: {a_resp.json().get('status')}")
                print("\n🔥 PASS: Full Split-API Triage flow verified!")
            else:
                print(f"❌ Stage 2 Error: {a_resp.status_code} - {a_resp.text}")
        else:
            print(f"❌ Stage 1 Error: {v_resp.status_code} - {v_resp.text}")
            
    except Exception as e:
        print(f"❌ Flow failed: {e}")

if __name__ == "__main__":
    test_split_api_flow()
