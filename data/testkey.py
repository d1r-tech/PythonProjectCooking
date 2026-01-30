# test_openrouter.py
import requests
import os

# 1. Проверьте что ключ в переменных окружения
api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("❌ OPENROUTER_API_KEY не установлен в переменных окружения")
    print("Установите: export OPENROUTER_API_KEY='ваш_ключ'")
    exit(1)

print(f"Ключ найден (длина: {len(api_key)})")

# 2. Простой тестовый запрос
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "FoodHub Test"
}

payload = {
    "model": "meta-llama/llama-3.2-3b-instruct:free",
    "messages": [
        {"role": "user", "content": "Привет, как дела?"}
    ],
    "max_tokens": 50
}

try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=10
    )

    print(f"Статус: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("✅ API работает!")
        print(f"Ответ: {data['choices'][0]['message']['content']}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(f"Ответ: {response.text[:500]}")

except Exception as e:
    print(f"❌ Ошибка соединения: {e}")