import os
import huggingface_hub
from huggingface_hub import from_pretrained_keras

print("HF_TOKEN in env:", "HF_TOKEN" in os.environ)
token = huggingface_hub.get_token()
print("HF Token found:", bool(token))

if token:
    try:
        model = from_pretrained_keras("google/hear")
        print("Model loaded successfully!")
    except Exception as e:
        print("Error loading model:", repr(e))
else:
    print("No token found.")
