import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_API_KEY")

client = InferenceClient(
    model="meta-llama/Llama-3.2-3B-Instruct",
    token=HF_TOKEN,
)

def generate_ai_reply(prompt):
    return "AI temporarily disabled. Backend is working."

def generate_ai_title(prompt):
    return "New Conversation"
