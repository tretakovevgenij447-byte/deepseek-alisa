import os
import asyncio
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL_NAME = "llama-3.1-8b-instant"  # Быстрая стабильная модель

@app.post("/")
async def main(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    user_text = ""
    try:
        user_text = body["request"]["original_utterance"]
    except (KeyError, TypeError):
        pass

    if not user_text.strip():
        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {"end_session": False, "text": "Я слушаю. Задайте свой вопрос."}
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json={
                        "model": MODEL_NAME,
                        "messages": [{"role": "user", "content": user_text}],
                        "max_tokens": 400  # Ограничиваем длину ответа, чтобы уложиться в лимит Алисы
                    },
                    timeout=3.8
                ),
                timeout=3.9
            )
            
            if response.status_code == 429:
                answer = "Слишком много запросов. Подождите минуту."
            else:
                response_data = response.json()
                if "error" in response_data:
                    answer = f"Ошибка API: {response_data['error'].get('message', 'Неизвестно')}"
                elif "choices" not in response_data or not response_data["choices"]:
                    answer = "Нейросеть временно недоступна."
                else:
                    answer = response_data["choices"][0]["message"]["content"]

    except (asyncio.TimeoutError, httpx.TimeoutException):
        answer = "Извини, я задумалась. Повтори вопрос, пожалуйста."
    except Exception as e:
        answer = f"Ошибка: {str(e)[:50]}"

    # Защитное обрезание текста до 1024 символов для соблюдения лимитов Алисы
    answer = answer[:1020].strip()

    return {
        "version": body.get("version", "1.0"),
        "session": body.get("session", {}),
        "response": {"end_session": False, "text": answer}
    }
