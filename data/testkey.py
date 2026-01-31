import requests

API_KEY = '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'

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "FoodHub Test"
}

# АКТУАЛЬНЫЕ РАБОЧИЕ МОДЕЛИ (январь 2025):
MODELS_TO_TRY = [
    "google/gemma-2-2b-it:free",  # ← ГЕММА 2 (новое название)
    "microsoft/phi-3.5-mini-instruct:free",  # ← PHI 3.5 (новое)
    "qwen/qwen2.5-coder-7b-instruct:free",  # ← QWEN 2.5
    "meta-llama/llama-3.2-3b-instruct",  # ← БЕЗ :free
    "mistralai/mistral-7b-instruct-v0.3:free",
    "nousresearch/hermes-3-llama-3.1-8b:free"
]

for model in MODELS_TO_TRY:
    print(f"\n🔧 Тестируем: {model}")

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Привет, ответь 'работает' если слышишь"}
        ],
        "max_tokens": 30
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"   Статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            answer = data['choices'][0]['message']['content']
            print(f"   ✅ РАБОТАЕТ! Ответ: {answer}")
            print(f"\n🎉 ИСПОЛЬЗУЙТЕ: {model}")
            break
        elif response.status_code == 429:
            print(f"   ⚠️  Лимит (429). Попробуем следующую...")
        elif response.status_code == 404:
            print(f"   ❌ Модель не найдена (404)")
        else:
            print(f"   ❌ Ошибка {response.status_code}: {response.text[:100]}")

    except Exception as e:
        print(f"   ❌ Исключение: {e}")