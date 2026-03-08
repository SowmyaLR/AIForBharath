import boto3
import json
import time
import sys

# Configuration
ENDPOINT_NAME = "vaidyasaarathi-demo-v2-medgemma-endpoint"
REGION = "ap-south-1"

# Sample Input Data (Production Scenario)
transcript = "I have been coughing for two days and I am having a lot of trouble breathing. My chest feels very tight and I can't catch my breath even when resting."
risk_data = {"score": 8.2}
vitals = {"temperature": 101.2, "spo2": 92, "heart_rate": 110}
age = 45

# Build the EXACT production prompt from server/services/ai_service.py
vitals_str = ", ".join([f"{k}: {v}" for k, v in vitals.items() if v])
age_info = f"Age: {age}" if age else "Age: Not provided"

prompt_content = f"""
        You are a Senior Clinical Triage Specialist AI. Your goal is to generate professional, detailed, and actionable medical documentation.

        --- 
        FEW-SHOT EXAMPLE OF EXPECTED QUALITY:
        
        INPUT:
        Transcript: "I've had a really bad cough for 3 days, it's getting worse and I'm feeling a bit short of breath now. My chest feels slightly tight."
        Age: 65
        Vitals: Temperature: 38.5, BP: 130/85, HR: 95, SpO2: 94, RR: 22
        Acoustic Score: 6.5/10
        
        OUTPUT:
        {{
          "soap_note": {{
            "subjective": "Patient reports a productive cough of 3 days duration, increasing in severity. Acute onset of shortness of breath and chest tightness today. Denies chest pain, hemoptysis, or known sick contacts.",
            "objective": "Patient is febrile (38.5°C) and tachypneic (RR 22). Mild respiratory effort audible in audio. Moderate oxygen desaturation (SpO2 94%) on room air. HeAR Acoustic Deviation Score (6.5/10) indicates significant acoustic instability consistent with moderate respiratory distress.",
            "assessment": "Likely lower respiratory tract infection (e.g., Pneumonia) vs. Acute Bronchitis. Triage Tier: URGENT due to combination of fever, tachypnea, and oxygen desaturation.",
            "plan": "1. Immediate physician evaluation. 2. Initiate supplemental oxygen if SpO2 < 94%. 3. Obtain Chest X-ray and CBC with diff. 4. Monitor vitals and work of breathing every 15 minutes."
          }},
          "metadata": {{
            "symptoms": [
              {{"name": "cough", "severity": "SEVERE", "category": "RESPIRATORY"}},
              {{"name": "shortness of breath", "severity": "MODERATE", "category": "RESPIRATORY"}}
            ],
            "triage_tier": "URGENT",
            "clinical_reasoning": "Escalated to URGENT due to hypoxia (94%) and systemic signs (fever) paired with high acoustic instability.",
            "red_flags_present": true
          }}
        }}
        ---

        Now, process the following real-time patient data following the EXACT same professional format and detail level:

        PATIENT DATA:
        Transcript: \"\"\"{transcript}\"\"\"
        {age_info}
        Vitals: {vitals_str}
        HeAR Acoustic Deviation Score: {risk_data['score']:.1f}/10

        REQUIREMENTS:
        1. Return ONLY valid JSON.
        2. DO NOT summarize instructions. Provide ACTUAL clinical content.
        3. Subjective: Include onset, duration, and specific symptoms mentioned.
        4. Objective: Synthesize the vitals AND the Acoustic Score into a clinical observation.
        5. Assessment: Provide a context-aware reasoning with potential differential diagnoses.
        6. Plan: List 3-4 specific, actionable clinical next steps.
        7. No markdown, no pre-text, no post-text.

        JSON OUTPUT:
        """

# Correct Gemma Chat Template Wrapper
prompt = f"<start_of_turn>user\n{prompt_content}<end_of_turn>\n<start_of_turn>model\n"

sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

def test_async_inference():
    print(f"🚀 Starting Async Inference on: {ENDPOINT_NAME}")
    
    # 1. Prepare Payload & Upload to S3
    payload_body = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200}
    }
    
    import uuid
    import os
    request_id = str(uuid.uuid4())
    async_bucket = os.getenv("SAGEMAKER_ASYNC_BUCKET")
    
    if not async_bucket:
        print("❌ ERROR: SAGEMAKER_ASYNC_BUCKET env var not set.")
        return

    input_key = f"medgemma-inputs/{request_id}.json"
    input_location = f"s3://{async_bucket}/{input_key}"

    try:
        print(f"📤 Uploading input to: {input_location}")
        s3_client.put_object(
            Bucket=async_bucket,
            Key=input_key,
            Body=json.dumps(payload_body),
            ContentType="application/json"
        )

        # 2. Trigger Async Inference
        response = sagemaker_runtime.invoke_endpoint_async(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            InputLocation=input_location
        )
        
        output_location = response["OutputLocation"]
        print(f"📡 Submitted! Output will appear at: {output_location}")
        
        # Parse S3 URI
        output_bucket = output_location.split("/")[2]
        output_key = "/".join(output_location.split("/")[3:])
        
        # 3. Poll for Result
        print("⏳ Polling for result... (this triggers scale-up if instances=0)")
        for attempt in range(60):
            try:
                resp = s3_client.get_object(Bucket=output_bucket, Key=output_key)
                result = json.loads(resp["Body"].read().decode("utf-8"))
                print("\n✅ SUCCESS! Result received:")
                print("-" * 50)
                if isinstance(result, list):
                    print(result[0].get("generated_text", ""))
                else:
                    print(result.get("generated_text", str(result)))
                print("-" * 50)
                
                # Cleanup
                s3_client.delete_object(Bucket=async_bucket, Key=input_key)
                return
            except s3_client.exceptions.NoSuchKey:
                if attempt % 3 == 0:
                    print(f"   ...waiting ({attempt * 10}s elapsed)")
                time.sleep(10)
        
        print("\n❌ TIMEOUT: Result did not appear within 10 minutes.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_async_inference()
