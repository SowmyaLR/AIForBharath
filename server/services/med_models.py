import random
import torch
import librosa
import numpy as np
import io
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# Global model loaders (lazy loading recommended for production, but init here for demo)
# Using 'openai/whisper-small' as a proxy for MedASR since MedASR weights aren't public/auth-free yet.
print("Loading ASR model...")
asr_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-small")

# Using 'google/gemma-2b-it' as the reasoning engine (MedGemma proxy).
# REPLACED by Ollama 'medgemma' content.
print("Expert model will be called via Ollama API...")
import warnings
# Suppress librosa/audioread warnings about deprecated features and PySoundFile fallbacks
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
# Suppress transformers deprecation warnings
warnings.filterwarnings("ignore", message=".*return_token_timestamps.*")

# tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b-it")
# model = AutoModelForCausalLM.from_pretrained("google/gemma-2b-it", device_map="auto")

import tempfile
import os

def load_audio_robust(file_bytes):
    # Write to temp file to help libraries detect format (especially webm)
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    
    try:
        # librosa.load is more robust than sf.read for webm (uses ffmpeg if avail)
        # Load at 16k for Whisper compatibility
        data, samplerate = librosa.load(tmp_path, sr=16000)
        return data, samplerate
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def transcribe_audio(file_bytes):
    """
    Performs ASR using local Whisper model.
    """
    try:
        print(f"DEBUG: Starting Transcribe ({len(file_bytes)} bytes)...")
        data, samplerate = load_audio_robust(file_bytes)
            
        # Enable translation to English (X -> English)
        print("DEBUG: Running Whisper Inference (Medium)...")
        result = asr_pipeline(data, generate_kwargs={"task": "translate"})
        text = result.get("text", "")
        print(f"DEBUG: Transcribe Complete: {text[:50]}...")
        
        return {
            "text": text,
            # Note: HF pipeline doesn't return overall confidence by default. 
            # Real implementation requires calculating avg log-probs of tokens.
            # Keeping as placeholder for now since text is real.
            "confidence": 0.95 
        }
    except Exception as e:
        print(f"ASR Error: {e}")
        return {"text": "Error processing audio. Ensure FFmpeg is installed.", "confidence": 0.0}

def analyze_cough(file_bytes):
    """
    Simulates HeAR (Health Acoustic Representations) model.
    """
    try:
        print("DEBUG: Starting Acoustic Analysis...")
        data, sr = load_audio_robust(file_bytes)
        
        # Simple acoustic features
        zcr = np.mean(librosa.feature.zero_crossing_rate(data))
        
        # Heuristic: High ZCR might indicate noisy/cough-like sound
        risk_score = min(zcr * 5, 0.99) # Arbitrary scaling for demo
        print(f"DEBUG: Acoustic Analysis Complete. Score: {risk_score}")
        
        return {
            "risk_score": float(risk_score),
            "acoustic_markers": ["abnormal_zcr"] if risk_score > 0.5 else ["normal_acoustics"],
            "interpretation": "Acoustic anomalies detected." if risk_score > 0.5 else "Within normal limits."
        }
    except Exception as e:
        print(f"HeAR Error: {e}")
        return {
            "risk_score": 0.0,
            "interpretation": "Error analyzing audio."
        }

    return {
        "soap_note": response_text.replace(prompt, "").strip(),
        "generated_by": "MedGemma (Ollama)"
    }

def generate_soap_note(transcript, risk_data):
    """
    Uses MedGemma (via Ollama) to generate a SOAP note.
    Make sure 'ollama run medgemma' is running.
    """
    import requests
    import json
    
    print("DEBUG: Generating SOAP Note via Ollama...")
    prompt = f"""
    You are an expert medical AI assistant.
    Task: Create a professional SOAP note based on the patient transcript and acoustic analysis.
    
    Patient Transcript: "{transcript}"
    Acoustic Risk Score: {risk_data['risk_score']:.2f} ({risk_data['interpretation']})
    
    Format:
    SUBJECTIVE: ...
    OBJECTIVE: ...
    ASSESSMENT: ...
    PLAN: ...
    
    Generate ONLY the SOAP note. Do not include introductory text.
    """
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "alibayram/medgemma",
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        result = response.json()
        soap_text = result.get("response", "Error generating note.")
        print("DEBUG: SOAP Note Generated.")
        
        return {
            "soap_note": soap_text.strip(),
            "generated_by": "MedGemma (Ollama)"
        }
    except Exception as e:
        print(f"Ollama Error: {e}")
        return {
            "soap_note": "System Error: Ensure Ollama is running with 'medgemma' model.",
            "generated_by": "Error"
        }
