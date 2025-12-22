# chat/ai_model.py
import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_API_KEY")

client = InferenceClient(
    model="meta-llama/Llama-3.2-3B-Instruct",
    token=HF_TOKEN,
)

def generate_ai_reply(prompt):
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"AI Error: {e}"

def generate_ai_title(prompt):
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Generate a short title: {prompt}"}],
            max_tokens=25,
        )
        return response.choices[0].message["content"]
    except Exception:
        return "Untitled"
