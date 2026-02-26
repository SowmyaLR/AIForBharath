import os
import io
import re
import librosa
import numpy as np
import tempfile
import time
import requests
import warnings
import tensorflow as tf
from huggingface_hub import snapshot_download
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
from faster_whisper import WhisperModel

# Suppress warnings as per prototype
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
warnings.filterwarnings("ignore", message=".*return_token_timestamps.*")

import json

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Clinical Triage Constants
TRIAGE_BUCKETS = {
    "EMERGENCY": 4,   # 🔴 Immediate risk
    "URGENT": 3,      # 🟠 High risk
    "SEMI_URGENT": 2, # 🟡 Needs evaluation
    "ROUTINE": 1      # 🟢 Low risk
}

# Score mapping for UI legacy compatibility (0-100)
BUCKET_SCORES = {
    "EMERGENCY": 95,
    "URGENT": 75,
    "SEMI_URGENT": 45,
    "ROUTINE": 15
}

CRITICAL_SYMPTOMS = ["chest pain", "severe breathlessness", "unconscious", "seizure", "slurred speech", "difficulty speaking", "cannot speak", "sudden weakness", "stroke", "paralysis", "vision loss"]
HIGH_SYMPTOMS = ["breathlessness", "persistent vomiting", "high fever", "severe headache", "confusion", "visual disturbances", "blurred vision"]
MODERATE_SYMPTOMS = ["dizziness", "body pain", "cough", "fatigue", "lightheadedness", "nausea"]

CATEGORY_SPECIALTIES = {
    "cardiac": ["chest pain"],
    "respiratory": ["breathlessness", "severe breathlessness", "cough"],
    "neurological": ["unconscious", "seizure", "slurred speech", "sudden weakness", "stroke", "confusion", "severe headache"],
}

class AIServiceError(Exception):
    pass
class AudioProcessor:
    def __init__(self):
        # 1. Initialize Whisper Model (faster-whisper)
        print("Loading ASR model (faster-whisper medium)...")
        # Use CPU with int8 quantization for high performance on both CPU and Apple Silicon
        # 'auto' will choose the best device available.
        self.asr_model = WhisperModel("medium", device="auto", compute_type="int8")
        
        # 2. Initialize HeAR (Official Keras)
        print("Loading HeAR model (HuggingFace)...")
        try:
            # Download full repo and load as SavedModel
            model_dir = snapshot_download("google/hear")
            model = tf.saved_model.load(model_dir)
            self.hear_serving_signature = model.signatures['serving_default']
            print("HeAR model loaded successfully!")
        except Exception as e:
            print(f"Error loading HeAR model: {e}")
            self.hear_serving_signature = None

    def load_audio_robust(self, file_bytes):
        """Robustly loads audio using temp file as per user prototype"""
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            # librosa.load at 16k for Whisper compatibility
            data, samplerate = librosa.load(tmp_path, sr=16000)
            return data, samplerate
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def transcribe(self, audio_bytes: bytes, language: str) -> str:
        """Performs ASR with optimized faster-whisper inference"""
        try:
            print(f"\n[AI DEBUG] Starting Transcribe ({len(audio_bytes)} bytes)...")
            data, samplerate = self.load_audio_robust(audio_bytes)
            
            # Use lowercase for language
            lang_code = language.lower()
            
            # WhisperModel expects 'en', 'ta', etc. but we can also use 'english', 'tamil'
            # Mapping common languages to codes for faster-whisper robustness
            lang_map = {
                "english": "en",
                "tamil": "ta",
                "hindi": "hi",
                "telugu": "te"
            }
            whisper_lang = lang_map.get(lang_code, lang_code)
            
            # Task selection
            task = "transcribe" if lang_code == "english" else "translate"
            
            print(f"[AI DEBUG] Running faster-whisper Inference (Task: {task}, Language: {whisper_lang})...")
            
            # faster-whisper transcribe returns a generator of segments
            segments, info = self.asr_model.transcribe(
                data,
                task=task,
                language=whisper_lang,
                beam_size=5,
                repetition_penalty=1.1,
                no_repeat_ngram_size=3,
                condition_on_previous_text=False # prevents hallucinations
            )
            
            # Collect text from segments
            text_parts = [segment.text for segment in segments]
            text = " ".join(text_parts).strip()
            
            print(f"[AI DEBUG] Transcribe Result: {text[:200]}...")
            return text
        except Exception as e:
            print(f"[AI DEBUG] ASR Error: {e}")
            return "Error processing audio."

    def detect_anomalies(self, audio_bytes: bytes) -> dict:
        """Production-Safe Temporal Stability Strategy"""
        try:
            print(f"\n{'='*30}\n[AI TRACE] TEMPORAL STABILITY ANALYSIS START\n{'='*30}")
            t_start = time.time()
            data, sr = self.load_audio_robust(audio_bytes)
            
            if self.hear_serving_signature:
                # 1. Split audio into 1-second chunks (prototype logic says 5-15 chunks)
                chunk_sec = 1.0
                chunk_size = int(sr * chunk_sec)
                chunks = [data[i:i+chunk_size] for i in range(0, len(data)-chunk_size, chunk_size)]
                
                if not chunks:
                    chunks = [data] # fallback if audio < 1s
                
                print(f"[AI TRACE] Audio split into {len(chunks)} temporal chunks.")
                
                # 2. Extract and Normalize Embeddings
                chunk_embeddings = []
                for i, chunk in enumerate(chunks):
                    # Pad chunk to 2s if needed, or just follow user logic of flatten/norm
                    input_tensor = tf.constant(np.expand_dims(chunk, axis=0), dtype=tf.float32)
                    emb = self.hear_serving_signature(x=input_tensor)['output_0'].numpy().flatten()
                    
                    # Normalize to unit vector (critical for cosine similarity)
                    norm = np.linalg.norm(emb)
                    if norm > 0:
                        emb = emb / norm
                    chunk_embeddings.append(emb)
                
                chunk_embeddings = np.vstack(chunk_embeddings)
                
                # 3. Measure Internal Variability (Pairwise Cosine Similarity)
                # High similarity = stable phonation. Low similarity = instability/anomalies.
                similarity_matrix = cosine_similarity(chunk_embeddings)
                avg_similarity = np.mean(similarity_matrix)
                deviation_score = 1.0 - avg_similarity
                
                # Scale to 0-10 based on user's empirical multiplier (50)
                risk_score = round(min(10.0, deviation_score * 50), 1)
                
                # Naming updated per user request to 'Acoustic Deviation Score'
                interpretation = f"HeAR Acoustic Analysis: Acoustic Deviation Score {risk_score}/10"
            else:
                print("\n>>> WARNING: LIBROSA FALLBACK TRIGGERED (HEAR UNAVAILABLE) <<<")
                zcr = np.mean(librosa.feature.zero_crossing_rate(data))
                risk_score = round(min(zcr * 50, 10.0), 1) 
                interpretation = f"Acoustic Feature Baseline: Deviation Score {risk_score}/10 (Fallback)"
            
            t_total = time.time() - t_start
            print(f"[AI TRACE] Average Chunk Similarity: {avg_similarity:.4f}" if self.hear_serving_signature else "[AI TRACE] Fallback Active")
            print(f"[AI TRACE] Final Stability Score (0-10): {risk_score}")
            print(f"{'='*30}\n[AI TRACE] ANALYSIS COMPLETE ({t_total:.2f}s)\n{'='*30}\n")
            
            return {
                "score": float(risk_score),
                "interpretation": interpretation,
                "findings": [interpretation]
            }
        except Exception as e:
            print(f"[AI TRACE] Analysis Error: {e}")
            import traceback
            traceback.print_exc()
            return {"score": 0.0, "interpretation": "Error analyzing audio.", "findings": []}

    def generate_soap_note(self, transcript: str, risk_data: dict) -> dict:
        """Prototype generation logic with strict JSON output"""
        print("\n[AI DEBUG] Generating SOAP Note via Ollama...")
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
        
        print(f"[AI DEBUG] Ollama Prompt Built ({len(prompt)} chars)")
        
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": "alibayram/medgemma",
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            soap_text = result.get("response", "Error generating note.")
            print(f"\n[AI DEBUG] --- RAW OLLAMA RESPONSE START ---\n{soap_text}\n[AI DEBUG] --- RAW OLLAMA RESPONSE END ---\n")
            
            # 1. Clean response (remove markdown fences and trailing text)
            clean_response = soap_text.strip()
            # Find the outermost { } to handle any preamble/postamble
            start_idx = clean_response.find('{')
            end_idx = clean_response.rfind('}')
            
            full_json = None
            if start_idx != -1 and end_idx != -1:
                try:
                    json_str = clean_response[start_idx:end_idx+1]
                    full_json = json.loads(json_str)
                    print("[AI DEBUG] Successfully parsed JSON from structure")
                except Exception as e:
                    print(f"[AI DEBUG] JSON parse failed: {e}")

            # 2. Extract sections with fallbacks
            meta_data = {}
            subjective, objective, assessment, plan = "", "", "", ""

            if full_json:
                # Support both new and old structures for backward compatibility
                soap_obj = full_json.get("soap_note", full_json)
                subjective = soap_obj.get("subjective", full_json.get("SUBJECTIVE", ""))
                objective = soap_obj.get("objective", full_json.get("OBJECTIVE", ""))
                assessment = soap_obj.get("assessment", full_json.get("ASSESSMENT", ""))
                plan = soap_obj.get("plan", full_json.get("PLAN", ""))
                meta_data = full_json.get("metadata", full_json.get("METADATA", full_json))
            else:
                # Fallback to tag-based if JSON fails
                subjective = self._extract_section(soap_text, "SUBJECTIVE")
                objective = self._extract_section(soap_text, "OBJECTIVE")
                assessment = self._extract_section(soap_text, "ASSESSMENT")
                plan = self._extract_section(soap_text, "PLAN")
                meta_json = self._extract_section(soap_text, "METADATA")
                try:
                    meta_data = json.loads(meta_json)
                except:
                    print(f"[AI DEBUG] Metadata JSON parsing failed.")

            # New Bucket-Based Triage Flow
            final_tier, assigned_specialty = self._calculate_bucket_triage(
                transcript=transcript,
                ai_meta=meta_data,
                acoustic_score=risk_data['score']
            )

            final_analysis = {
                "soap": {
                    "subjective": subjective,
                    "objective": objective,
                    "assessment": assessment,
                    "plan": plan
                },
                "specialty": assigned_specialty, 
                "risk_score": BUCKET_SCORES.get(final_tier, 0),
                "triage_tier": final_tier
            }
            print(f"[AI DEBUG] Final Parsed Analysis: {assigned_specialty}, Tier: {final_tier}")
            return final_analysis
        except Exception as e:
            print(f"[AI DEBUG] Ollama Error: {e}")
            return {"soap": {"subjective": "Error generating note."}, "specialty": "General Medicine", "risk_score": 0}

    def _calculate_bucket_triage(self, transcript: str, ai_meta: dict, acoustic_score: float) -> tuple:
        """Implements the 4-tier bucket flow: AI -> Guardrail -> Acoustic Escalation"""
        # 1. Start with AI Classification
        ai_tier = ai_meta.get("triage_tier", "ROUTINE").upper()
        if ai_tier not in TRIAGE_BUCKETS:
            ai_tier = "ROUTINE"
            
        current_rank = TRIAGE_BUCKETS[ai_tier]
        print(f"[TRIAGE] Step 1: MedGemma Initial Tier -> {ai_tier}")

        # 2. Backend Guardrail Override (Deterministic)
        transcript_lower = transcript.lower()
        if any(kw in transcript_lower for kw in CRITICAL_SYMPTOMS):
            if current_rank < TRIAGE_BUCKETS["EMERGENCY"]:
                print(f"[TRIAGE] Step 2: Guardrail Triggered! Escalating to EMERGENCY (Critical Keyword detected)")
                current_rank = TRIAGE_BUCKETS["EMERGENCY"]
        elif any(kw in transcript_lower for kw in HIGH_SYMPTOMS):
            if current_rank < TRIAGE_BUCKETS["URGENT"]:
                print(f"[TRIAGE] Step 2: Guardrail Triggered! Escalating to URGENT (High-risk Keyword detected)")
                current_rank = TRIAGE_BUCKETS["URGENT"]

        # 3. Optional Acoustic Escalation (max +1 level)
        # High acoustic deviation (> 7.0) pushes it up one bucket
        if acoustic_score > 7.0:
            if current_rank < TRIAGE_BUCKETS["EMERGENCY"]:
                original_rank = current_rank
                current_rank += 1
                new_tier = [k for k, v in TRIAGE_BUCKETS.items() if v == current_rank][0]
                print(f"[TRIAGE] Step 3: Acoustic Escalation! High deviation ({acoustic_score}) pushes tier +1 to {new_tier}")

        # Final Bucket determination
        final_tier = [k for k, v in TRIAGE_BUCKETS.items() if v == current_rank][0]
        
        # 4. Specialty Assignment (based on symptoms metadata)
        symptoms = ai_meta.get("symptoms", [])
        primary_category = "general"
        if symptoms:
            # Simple heuristic: last or most severe category
            primary_category = symptoms[0].get("category", "general").lower()

        specialties = {
            "cardiac": "Cardiology",
            "respiratory": "Pulmonology",
            "neurological": "Neurology",
            "general": "General Medicine"
        }
        assigned_specialty = specialties.get(primary_category, "General Medicine")

        return final_tier, assigned_specialty

    def _extract_section(self, text, section):
        # Matches [SECTION] or **[SECTION]** or variations
        pattern = fr"\[{section}\]\s*(.*?)(?=\s*\n?\[[A-Z]+\]|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            content = match.group(1).strip()
            # Remove any lingering markdown fences if it's a metadata block
            if section == "METADATA":
                content = re.sub(r"```[a-z]*\n?", "", content).replace("```", "").strip()
            return content
            
        # Fallback for older formats or bolding variations
        fallback_pattern = fr"(?i)\**{section}\**[\s:-]*(.*?)(?=\s*\n?\**[A-Z]{{3,}}\**[\s:-]|$)"
        fallback_match = re.search(fallback_pattern, text, re.DOTALL)
        if fallback_match:
            return fallback_match.group(1).strip()

        print(f"[AI DEBUG] Extraction failure for {section}. Text length: {len(text)}")
        return f"Clinical assessment for {section}."
