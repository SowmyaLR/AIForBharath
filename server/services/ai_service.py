import os
import io
import librosa
import numpy as np
import tempfile
import time
import requests
import warnings
import tensorflow as tf
from huggingface_hub import from_pretrained_keras
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

# Suppress warnings as per prototype
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
warnings.filterwarnings("ignore", message=".*return_token_timestamps.*")

import json

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Clinical Triage Constants
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
        # 1. Initialize Whisper
        print("Loading ASR model (Whisper)...")
        self.asr_pipeline = pipeline(
            "automatic-speech-recognition", 
            model="openai/whisper-small", 
            device="cpu"
        )
        
        # 2. Initialize HeAR (Official Keras)
        print("Loading HeAR model (Keras)...")
        try:
            model = from_pretrained_keras("google/hear")
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
        """Performs ASR as per prototype"""
        try:
            print(f"\n[AI DEBUG] Starting Transcribe ({len(audio_bytes)} bytes)...")
            data, samplerate = self.load_audio_robust(audio_bytes)
            
            print(f"[AI DEBUG] Running Whisper Inference (Language: {language})...")
            result = self.asr_pipeline(data, generate_kwargs={"task": "translate"})
            text = result.get("text", "")
            print(f"[AI DEBUG] Transcribe/Translate Result: {text[:100]}...")
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
            {{"name": "symptom name", "severity": "mild|moderate|severe", "category": "cardiac|respiratory|neurological|general"}}
          ],
          "duration": "patient mentioned duration",
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
            
            # Extract metadata and calculate composite risk
            meta_json = self._extract_section(soap_text, "METADATA")
            symptoms = []
            if "Bioacoustic" not in meta_json: # basic check if it's actual content
                try:
                    meta_data = json.loads(meta_json)
                    symptoms = meta_data.get("symptoms", [])
                except:
                    print(f"[AI DEBUG] Metadata JSON parsing failed.")

            composite_risk, assigned_specialty = self._calculate_composite_score(symptoms, risk_data['score'])

            final_analysis = {
                "soap": {
                    "subjective": self._extract_section(soap_text, "SUBJECTIVE"),
                    "objective": self._extract_section(soap_text, "OBJECTIVE"),
                    "assessment": self._extract_section(soap_text, "ASSESSMENT"),
                    "plan": self._extract_section(soap_text, "PLAN")
                },
                "specialty": assigned_specialty, 
                "risk_score": composite_risk
            }
            print(f"[AI DEBUG] Final Parsed Analysis: {final_analysis}")
            return final_analysis
        except Exception as e:
            print(f"[AI DEBUG] Ollama Error: {e}")
            return {"soap": {"subjective": "Error generating note."}, "specialty": "General Medicine", "risk_score": 0}

    def _calculate_composite_score(self, symptoms: list, acoustic_score: float) -> tuple:
        """Calculates 60/40 weighted risk and assigns specialty"""
        # 1. Calculate Symptom Risk (Max points based on tiers)
        max_symptom_val = 0
        primary_category = "general"
        
        for s in symptoms:
            name = s.get("name", "").lower()
            cat = s.get("category", "general").lower()
            
            val = 10 # Default mild
            matched_tier = "Mild"
            
            # Use partial matching for robustness
            if any(cs in name or name in cs for cs in CRITICAL_SYMPTOMS): 
                val = 90
                matched_tier = "CRITICAL"
            elif any(hs in name or name in hs for hs in HIGH_SYMPTOMS): 
                val = 65
                matched_tier = "HIGH"
            elif any(ms in name or name in ms for ms in MODERATE_SYMPTOMS): 
                val = 35
                matched_tier = "MODERATE"
            
            print(f"[RISK MATH] Symptom: '{name}' -> Tier: {matched_tier} ({val} pts)")
            
            if val > max_symptom_val:
                max_symptom_val = val
                primary_category = cat

        # 2. Weighted Composite Calculation (Total 0-100)
        # Total Risk = (Symptom Risk * 0.6) + (Acoustic Risk * 0.4)
        symptom_weight = max_symptom_val * 0.6
        acoustic_weight = (acoustic_score * 10) * 0.4
        total_risk = int(symptom_weight + acoustic_weight)
        
        print(f"[RISK MATH] ------------------------------------")
        print(f"[RISK MATH] Symptom Component (60%): {symptom_weight:.1f}")
        print(f"[RISK MATH] Acoustic Component (40%): {acoustic_weight:.1f} (Raw HeAR: {acoustic_score})")
        print(f"[RISK MATH] Final Composite Score: {total_risk}/100")
        print(f"[RISK MATH] ------------------------------------")
        
        # 3. Specialty Assignment
        specialties = {
            "cardiac": "Cardiology",
            "respiratory": "Pulmonology",
            "neurological": "Neurology",
            "general": "General Medicine"
        }
        assigned_specialty = specialties.get(primary_category, "General Medicine")
        
        return min(100, total_risk), assigned_specialty

    def _extract_section(self, text, section):
        import re
        # We now use a strict [TAG] format for better reliability
        # Matches [SECTION] or **[SECTION]** or variations
        pattern = fr"\[{section}\]\s*(.*?)(?=\s*\n?\[[A-Z]+\]|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
            
        # Fallback for older formats or bolding variations
        fallback_pattern = fr"(?i)\**{section}\**[\s:-]*(.*?)(?=\s*\n?\**[A-Z]{{3,}}\**[\s:-]|$)"
        fallback_match = re.search(fallback_pattern, text, re.DOTALL)
        if fallback_match:
            return fallback_match.group(1).strip()

        print(f"[AI DEBUG] Extraction failure for {section}. Text length: {len(text)}")
        return f"Clinical assessment for {section}."
