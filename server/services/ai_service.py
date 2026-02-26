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
        print("Loading ASR model (faster-whisper small)...")
        # Use CPU with int8 quantization for high performance on both CPU and Apple Silicon
        # 'auto' will choose the best device available.
        self.asr_model = WhisperModel("small", device="auto", compute_type="int8")
        
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
        """Prototype generation logic"""
        print("\n[AI DEBUG] Generating SOAP Note via Ollama...")
        prompt = f"""
        [SYSTEM]
        You are a highly efficient clinical triage AI.
        
        [INPUT DATA]
        Patient Transcript: "{transcript}"
        HeAR Acoustic Analysis: Acoustic Deviation Score {risk_data['score']:.1f}/10
        
        [INSTRUCTIONS]
        Generate a professional SOAP note and extract clinical metadata.
        Clinical weighting: Prioritize the Acoustic Deviation Score (>5.0) ONLY if symptoms are respiratory/cardiac (cough, breathlessness, chest pain). Otherwise, treat it as a secondary baseline.
        
        [REQUIRED FORMAT]
        [SUBJECTIVE]
        (Detailed symptoms, onset, and patient history)
        [OBJECTIVE]
        (Physical and bioacoustic findings. State the "Acoustic Deviation Score" here. 
        IMPORTANT: Infer clinical signs from the transcript, such as "audible respiratory distress," "clarity of speech," "reported level of pain," or specific visual signs mentioned by the patient.)
        [ASSESSMENT]
        (Clinical logic and context-aware differential diagnosis)
        [PLAN]
        (Next steps: tests, treatments, and follow-up)
        
        [METADATA]
        {{
          "symptoms": [
            {{"name": "...", "severity": "...", "category": "..."}}
          ],
          "triage_tier": "EMERGENCY|URGENT|SEMI_URGENT|ROUTINE",
          "clinical_reasoning": "Brief explanation for the tier",
          "red_flags_present": true|false
        }}
        
        GENERATE NOW. DO NOT INCLUDE INTRODUCTORY TEXT.
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
            print(f"[AI DEBUG] Ollama Raw Response Received ({len(soap_text)} chars)")
            
            # 1. Clean response (remove markdown fences)
            clean_response = soap_text.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].startswith("```"): lines = lines[:-1]
                clean_response = "\n".join(lines).strip()

            # 2. Distinguish between Tag-based and Full-JSON
            # If we see common tags, assume it's tag-based even if there's JSON inside
            is_tag_based = any(tag in soap_text for tag in ["[SUBJECTIVE]", "[OBJECTIVE]", "[ASSESSMENT]", "[PLAN]"])
            
            full_json = None
            if not is_tag_based:
                try:
                    # Handle cases where the whole response is a JSON object
                    json_match = re.search(r'(\{.*\})', clean_response, re.DOTALL)
                    if json_match:
                        maybe_json = json.loads(json_match.group(1))
                        # Verify it's a SOAP JSON and not just a metadata block
                        if any(k.upper() in maybe_json for k in ["SUBJECTIVE", "ASSESSMENT"]):
                            full_json = maybe_json
                            print("[AI DEBUG] Successfully parsed Full SOAP JSON from response")
                except:
                    pass

            # 3. Extract sections
            meta_data = {}
            if full_json:
                # Handle different casing from different models
                def get_case_insensitive(d, key, default=""):
                    for k, v in d.items():
                        if k.upper() == key.upper(): return v
                    return default

                subjective = get_case_insensitive(full_json, "SUBJECTIVE")
                objective = get_case_insensitive(full_json, "OBJECTIVE")
                assessment = get_case_insensitive(full_json, "ASSESSMENT")
                plan = get_case_insensitive(full_json, "PLAN")
                meta_data = get_case_insensitive(full_json, "METADATA", full_json)
            else:
                subjective = self._extract_section(soap_text, "SUBJECTIVE")
                objective = self._extract_section(soap_text, "OBJECTIVE")
                assessment = self._extract_section(soap_text, "ASSESSMENT")
                plan = self._extract_section(soap_text, "PLAN")
                meta_json = self._extract_section(soap_text, "METADATA")
                try:
                    # Clean embedded JSON if needed
                    clean_meta = meta_json.strip()
                    if "```" in clean_meta:
                        clean_meta = re.sub(r"```[a-z]*\n?", "", clean_meta).replace("```", "").strip()
                    # Ensure we have a valid JSON object
                    json_match = re.search(r'(\{.*\})', clean_meta, re.DOTALL)
                    if json_match:
                        meta_data = json.loads(json_match.group(1))
                    else:
                        meta_data = json.loads(clean_meta)
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
