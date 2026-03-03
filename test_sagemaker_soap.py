import boto3
import json
import time

# Configuration
ENDPOINT_NAME = "vaidyasaarathi-demo-v2-medgemma-endpoint"
REGION = "ap-south-1"

# Sample Input Data (Respiratory Distress Scenario)
transcript = "I have been coughing for two days and I am having a lot of trouble breathing. My chest feels very tight and I can't catch my breath even when resting."
risk_data = {"score": 8.2}
vitals = {"temperature": 101.2, "spo2": 92, "heart_rate": 110}

# Build the EXACT production prompt from server/services/ai_service.py
vitals_str = ", ".join([f"{k}: {v}" for k, v in vitals.items() if v])

prompt = f"""
        You are a highly reliable clinical triage AI operating in a structured medical documentation mode.

        You MUST return ONLY valid JSON.
        Do NOT include markdown.
        Do NOT include headings outside JSON.
        Do NOT include commentary.
        Do NOT include explanations before or after the JSON.
        The output MUST be fully parseable using a JSON parser.

        --------------------------------------
        INPUT DATA
        --------------------------------------
        Patient Transcript:
        \"\"\"{transcript}\"\"\"

        Patient Vitals:
        {vitals_str}

        HeAR Acoustic Deviation Score: {risk_data['score']:.1f}/10

        --------------------------------------
        CLINICAL WEIGHTING LOGIC
        --------------------------------------
        1. The Acoustic Deviation Score (>5.0) should be given higher clinical importance 
           ONLY when symptoms are respiratory or cardiac in nature 
           (e.g., cough, breathlessness, chest pain, palpitations).

        2. If symptoms are non-respiratory/non-cardiac, treat the Acoustic Score 
           as a secondary contextual baseline only.

        3. Infer observable clinical signs from transcript language where possible 
           (e.g., audible respiratory distress, speech clarity, distress level, 
           weakness, confusion, visible swelling, etc.).

        4. Use structured clinical reasoning consistent with real-world triage standards.

        --------------------------------------
        OUTPUT FORMAT (STRICT JSON ONLY)
        --------------------------------------

        {{
          "soap_note": {{
            "subjective": "Detailed symptoms, onset, duration, associated symptoms, relevant history.",
            "objective": "Observed or inferred findings including Acoustic Deviation Score and inferred clinical signs.",
            "assessment": "Context-aware clinical reasoning with prioritized differential diagnoses.",
            "plan": "Clear next steps: investigations, monitoring, referrals, treatment suggestions, follow-up."
          }},
          "metadata": {{
            "symptoms": [
              {{
                "name": "symptom name",
                "severity": "MILD|MODERATE|SEVERE",
                "category": "RESPIRATORY|CARDIAC|NEUROLOGICAL|GASTROINTESTINAL|GENERAL|OTHER"
              }}
            ],
            "triage_tier": "EMERGENCY|URGENT|SEMI_URGENT|ROUTINE",
            "clinical_reasoning": "Concise explanation for triage tier selection.",
            "red_flags_present": true|false
          }}
        }}

        --------------------------------------
        VALIDATION REQUIREMENTS
        --------------------------------------
        - The response MUST be valid JSON.
        - No trailing commas.
        - Boolean values must be true or false (lowercase).
        - No additional text outside the JSON object.
        - If formatting is incorrect, internally correct it before responding.

        Generate the structured clinical output now.
        """

# Invoke SageMaker
client = boto3.client("sagemaker-runtime", region_name=REGION)

print(f"🚀 Invoking SageMaker Endpoint: {ENDPOINT_NAME}...")
start_time = time.time()

try:
    response = client.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps({
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 800,
                "temperature": 0.1,
                "stop": ["</s>"]
            }
        })
    )

    end_time = time.time()
    latency = end_time - start_time
    
    result = json.loads(response["Body"].read().decode("utf-8"))
    
    # Hugging Face TGI returns a list of objects
    if isinstance(result, list):
        generated_text = result[0].get("generated_text", "")
    else:
        generated_text = result.get("generated_text", str(result))

    print(f"\n⏱️  RESPONSE TIME: {latency:.2f} seconds")
    print("\n✅ RAW RESPONSE FROM SAGEMAKER:")
    print("-" * 50)
    print(generated_text)
    print("-" * 50)

    # Try to parse as JSON to verify structure
    try:
        # Simple cleaning if it returned markdown fences
        json_clean = generated_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(json_clean)
        print("\n✨ FINAL JSON VALIDATION: SUCCESS")
        print(f"Triage Tier: {parsed['metadata']['triage_tier']}")
    except Exception as je:
        print(f"\n⚠️ JSON Extraction Warning: {je}")

except Exception as e:
    print(f"\n❌ Error invoking endpoint: {e}")
