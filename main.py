import os
import time
from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Адрес API Groq (очень быстрый и бесплатный)
API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Имя переменной оставили прежним, но в Render вы должны положить туда ключ Groq (gsk_...)
API_KEY = os.getenv("DEEPSEEK_API_KEY")

@app.post("/")
async def main(request: Request):
    body = {}
    try:
        body = await request.json()
        user_text = body["request"]["original_utterance"]
    except Exception:
        user_text = "Привет"

    start_time = time.time()
    
    try:
        # Отправляем запрос к Groq. Ждем не более 3.5 секунд
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile", # Быстрая и умная модель
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=3.5 
        )
        
        # Проверяем, успели ли мы уложиться в лимит Алисы (4.5 секунды)
        if time.time() - start_time > 4.0:
            answer = "Извини, я задумалась. Спроси еще раз, пожалуйста."
        else:
            response_data = response.json()
            
            if "error" in response_data:
                answer = f"Ошибка API: {response_data['error'].get('message', 'Неизвестная ошибка')}"
            elif "choices" not in response_data or not response_data["choices"]:
                answer = "Нейросеть временно недоступна. Попробуйте еще раз."
            else:
                answer = response_data["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        answer = "Нейросеть слишком долго думает. Попробуйте еще раз."
    except Exception:
        answer = "Произошла внутренняя ошибка. Попробуйте еще раз."

    # Возвращаем ответ в формате, который понимает Алиса
    return {
        "version": body.get("version", "1.0"),
        "session": body.get("session", {}),
        "response": {
            "end_session": False,
            "text": answer
        }
    }
