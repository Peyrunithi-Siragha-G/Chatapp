# chat/ai_model.py
import os
from huggingface_hub import InferenceClient


def get_client():
    token = os.getenv("HF_API_KEY")
    if not token:
        raise RuntimeError("HF_API_KEY is missing from environment")

    return InferenceClient(
        model="meta-llama/Llama-3.2-3B-Instruct",
        token=token,
    )


def generate_ai_reply(prompt):
    try:
        client = get_client()
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"AI Error: {str(e)}"


def generate_ai_title(prompt):
    try:
        client = get_client()
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Generate a short title: {prompt}"}],
            max_tokens=25,
        )
        return response.choices[0].message["content"]
    except Exception:
        return "Untitled"
