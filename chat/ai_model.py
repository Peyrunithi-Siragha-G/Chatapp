# chat/ai_model.py
import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_API_KEY")

client = InferenceClient(
    model="meta-llama/Llama-3.2-3B-Instruct",
    token=HF_TOKEN,
    base_url="https://router.huggingface.co"  # <-- REQUIRED
)

def generate_ai_reply(prompt):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"AI Error: {str(e)}"


def generate_ai_title(prompt):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=[
                {"role": "user", "content": f"Generate a short title for this: {prompt}"}
            ],
            max_tokens=25,
        )
        return response.choices[0].message["content"]
    except Exception:
        return "Untitled"
