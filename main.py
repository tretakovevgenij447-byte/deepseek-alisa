import os
import asyncio
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

# Адрес API Groq
API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Модель, которая точно работает и быстро отвечает
MODEL_NAME = "llama-3.1-8b-instant"  # или "openai/gpt-oss-20b"

@app.post("/")
async def main(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    # Безопасно извлекаем текст из запроса
    # original_utterance может отсутствовать при повторных запросах
    user_text = ""
    try:
        user_text = body["request"]["original_utterance"]
    except (KeyError, TypeError):
        pass

    # Если текста нет, отвечаем вежливо, но сессию не рвём
    if not user_text.strip():
        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {
                "end_session": False,
                "text": "Я слушаю. Задайте свой вопрос."
            }
        }

    try:
        # Жёсткий таймаут: 3.8 секунды. Если Groq не успел — Алиса получит ответ, а не ошибку.
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json={
                        "model": MODEL_NAME,
                        "messages": [{"role": "user", "content": user_text}],
                    },
                    timeout=3.8
                ),
                timeout=3.9  # Чуть больше, чем timeout у httpx
            )
            
            response_data = response.json()
            
            if "error" in response_data:
                answer = f"Ошибка API: {response_data['error'].get('message', 'Неизвестная ошибка')}"
            elif "choices" not in response_data or not response_data["choices"]:
                answer = "Нейросеть временно недоступна. Попробуйте ещё раз."
            else:
                answer = response_data["choices"][0]["message"]["content"]

    except (asyncio.TimeoutError, httpx.TimeoutException):
        # Если не успели — говорим об этом, но НЕ роняем сессию
        answer = "Извини, я задумалась. Повтори вопрос, пожалуйста."
    except Exception:
        answer = "Произошла внутренняя ошибка. Попробуй ещё раз."

    # Всегда возвращаем end_session: False, чтобы диалог продолжался
    return {
        "version": body.get("version", "1.0"),
        "session": body.get("session", {}),
        "response": {
            "end_session": False,
            "text": answer
        }
    }
