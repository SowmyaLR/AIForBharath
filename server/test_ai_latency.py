import os
import time
import json
import logging
import sys
from services.ai_service import AudioProcessor

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_latency():
    # 1. Initialize Processor
    print("--- 🦾 Initializing AI Processor ---")
    start_init = time.time()
    try:
        processor = AudioProcessor()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    print(f"✅ Initialized in {time.time() - start_init:.2f}s\n")

    # 2. Pick a test file
    # Choosing the largest file from storage/audio
    audio_file = "storage/audio/b0050b51-e733-489f-9c9b-082beef88b63_triage_1772519875995.webm"
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        # List files to help debug
        print(f"Files in storage/audio: {os.listdir('storage/audio')}")
        return

    with open(audio_file, "rb") as f:
        audio_bytes = f.read()

    print(f"--- 🎤 Testing with file: {audio_file} ({len(audio_bytes)/1024:.2f} KB) ---")

    # 3. Phase 1: Serialized Whisper + HeAR (Nitro Optimization)
    print("\n--- 📝 Phase 1: Serialized Whisper + HeAR ---")
    start_p1 = time.time()
    
    # 1. Whisper first
    transcript = processor.transcribe(audio_bytes, "english")
    
    # 2. HeAR second (Now with 3-point sampling)
    anomalies = processor.detect_anomalies(audio_bytes)
    
    p1_time = time.time() - start_p1
    print(f"✅ Phase 1 complete in {p1_time:.2f}s")
    
    # 4. Phase 2: SOAP Note Generation
    print("\n--- 🏥 Phase 2: SOAP Note Generation ---")
    mock_vitals = {
        "temperature": 38.5,
        "blood_pressure_systolic": 130,
        "blood_pressure_diastolic": 85,
        "heart_rate": 95,
        "oxygen_saturation": 94
    }
    mock_age = 45
    
    start_p2 = time.time()
    soap_result = processor.generate_soap_note(transcript, anomalies, mock_vitals, mock_age)
    p2_time = time.time() - start_p2
    print(f"✅ Phase 2 complete in {p2_time:.2f}s")

    # 5. Summary
    print("\n" + "="*50)
    print(f"  LOCAL PERFORMANCE SUMMARY (REFLECTING PRODUCTION)")
    print(f"  Total E2E Latency : {p1_time + p2_time:.2f}s")
    print(f"  Phase 1 (Parallel): {p1_time:.2f}s")
    print(f"  Phase 2 (AI)      : {p2_time:.2f}s")
    print("="*50)

if __name__ == "__main__":
    test_latency()
