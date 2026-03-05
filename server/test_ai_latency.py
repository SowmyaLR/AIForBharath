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

    # 3. Test Transcription (Whisper Medium)
    print("\n--- 📝 Running Transcription (Whisper Medium) ---")
    start_transcribe = time.time()
    transcript = processor.transcribe(audio_bytes, "english")
    transcribe_time = time.time() - start_transcribe
    print(f"✅ Transcription complete in {transcribe_time:.2f}s")
    print(f"Transcript snippet: {transcript[:100]}...")

    # 4. Test Acoustic Analysis (HeAR Vectorized)
    print("\n--- 🧬 Running Acoustic Analysis (HeAR Vectorized) ---")
    start_detect = time.time()
    anomalies = processor.detect_anomalies(audio_bytes)
    detect_time = time.time() - start_detect
    print(f"✅ Acoustic Analysis complete in {detect_time:.2f}s")

    # 5. Test SOAP Note Generation (Phase 2)
    print("\n--- 🏥 Running SOAP Note Generation (Phase 2: MedGemma) ---")
    # Mocking some vitals and age for the prompt
    mock_vitals = {
        "temperature": 38.5,
        "blood_pressure_systolic": 130,
        "blood_pressure_diastolic": 85,
        "heart_rate": 95,
        "oxygen_saturation": 94
    }
    mock_age = 45
    
    start_soap = time.time()
    soap_result = processor.generate_soap_note(transcript, anomalies, mock_vitals, mock_age)
    soap_time = time.time() - start_soap
    print(f"✅ SOAP Note Generation complete in {soap_time:.2f}s")
    print(f"Result Tier: {soap_result.get('triage_tier')}")

    # 6. Summary
    print("\n" + "="*50)
    print(f"  LOCAL PERFORMANCE SUMMARY")
    print(f"  Total E2E Latency:   {transcribe_time + detect_time + soap_time:.2f}s")
    print(f"  - Transcription:     {transcribe_time:.2f}s")
    print(f"  - Acoustic (Nitro):  {detect_time:.2f}s")
    print(f"  - SOAP Note (AI):    {soap_time:.2f}s")
    print("="*50)

if __name__ == "__main__":
    test_latency()
