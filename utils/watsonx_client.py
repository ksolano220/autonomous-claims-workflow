"""
IBM watsonx.ai client for Granite model inference.

Handles IAM token management and provides a simple interface
for the agents to call Granite for reasoning and decision-making.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

MODEL_ID = "ibm/granite-3-8b-instruct"

_token_cache = {"token": None, "expires_at": 0}


def _get_iam_token():
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={WATSONX_API_KEY}",
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["token"]


def generate(prompt, max_tokens=1024, temperature=0.1):
    token = _get_iam_token()
    resp = requests.post(
        f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy" if temperature == 0 else "sample",
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "stop_sequences": ["\n\n---"],
                "repetition_penalty": 1.1,
            },
            "model_id": MODEL_ID,
            "project_id": WATSONX_PROJECT_ID,
        },
    )
    resp.raise_for_status()
    return resp.json()["results"][0]["generated_text"].strip()


def chat(system_prompt, user_message, max_tokens=1024):
    prompt = (
        f"<|start_of_role|>system<|end_of_role|>{system_prompt}<|end_of_text|>\n"
        f"<|start_of_role|>user<|end_of_role|>{user_message}<|end_of_text|>\n"
        f"<|start_of_role|>assistant<|end_of_role|>"
    )
    return generate(prompt, max_tokens=max_tokens)
