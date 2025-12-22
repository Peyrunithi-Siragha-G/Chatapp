from huggingface_hub import InferenceClient
import os

client = InferenceClient(
    model="meta-llama/Llama-3.2-3B-Instruct",
    token=os.getenv("HF_API_KEY"),
    base_url="https://router.huggingface.co"
)

def generate_ai_reply(prompt):
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
    )
    return response.choices[0].message["content"]


def generate_ai_title(prompt):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": (
                    "Generate a very short, clear title (max 6 words) "
                    "for the following conversation:\n\n"
                    f"{prompt}"
                ),
            }
        ],
        max_tokens=20,
    )
    return response.choices[0].message["content"]
