import os
from fastapi import FastAPI, Request
import requests

app = FastAPI()

DEEPSEEK_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

@app.post("/")
async def main(request: Request):
    try:
        body = await request.json()
        user_text = body["request"]["original_utterance"]
    except Exception:
        user_text = "Привет"

    response = requests.post(
        DEEPSEEK_API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": user_text}],
        },
        timeout=4
    )
    
    response_data = response.json()
    
    if "error" in response_data:
        answer = f"Ошибка OpenRouter: {response_data['error'].get('message', 'Неизвестная ошибка')}"
    elif "choices" not in response_data or not response_data["choices"]:
        answer = "Нейросеть временно недоступна. Попробуйте еще раз."
    else:
        answer = response_data["choices"][0]["message"]["content"]

    return {
        "version": body.get("version", "1.0"),
        "session": body.get("session", {}),
        "response": {
            "end_session": False,
            "text": answer
        }
    }
