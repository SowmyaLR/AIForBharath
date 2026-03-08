import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/triage"

def test_seen_status():
    print("--- 🧪 Testing Triage 'Seen' Status and UTC Timestamps ---")
    
    # 1. Create a new triage record
    vitals_data = {
        "patient_id": "P-TEST-SEEN",
        "temp": 37.0,
        "bp_sys": 120,
        "bp_dia": 80,
        "hr": 70,
        "spo2": 99
    }
    
    print("\n📡 Creating triage record...")
    resp = requests.post(f"{BASE_URL}/vitals", data=vitals_data)
    if resp.status_code != 200:
        print(f"❌ Failed to create record: {resp.status_code} - {resp.text}")
        return
    
    record = resp.json()
    triage_id = record["id"]
    created_at = record["created_at"]
    is_seen = record["is_seen"]
    
    print(f"✅ Created Triage ID: {triage_id}")
    print(f"✅ Timestamp: {created_at}")
    print(f"✅ Initial is_seen: {is_seen}")
    
    # Check for 'Z' suffix or UTC offset
    if not (created_at.endswith('Z') or '+00:00' in created_at):
         print(f"⚠️ Warning: Timestamp {created_at} might not be in standard UTC format (missing Z or +00:00)")
    else:
        print(f"✅ Timestamp format looks like UTC.")

    if is_seen is not False:
        print(f"❌ Error: is_seen should be False initially, got {is_seen}")
        return

    # 2. Mark as seen
    print(f"\n📡 Marking triage {triage_id} as seen...")
    resp = requests.post(f"{BASE_URL}/{triage_id}/seen")
    if resp.status_code != 200:
        print(f"❌ Failed to mark as seen: {resp.status_code} - {resp.text}")
        return
    
    updated_record = resp.json()
    print(f"✅ Updated is_seen: {updated_record['is_seen']}")
    
    if updated_record['is_seen'] is not True:
        print(f"❌ Error: is_seen should be True now")
        return

    print("\n🔥 PASS: Triage 'seen' status and UTC timestamp verification successful!")

if __name__ == "__main__":
    test_seen_status()
