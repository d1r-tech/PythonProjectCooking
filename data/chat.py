import requests
import json
from flask import current_app, session
from functools import wraps

user_chats = {}


def get_user_id():
    """Получить идентификатор текущего пользователя"""
    from flask_login import current_user

    if current_user.is_authenticated:
        return f"user_{current_user.id}"

    if 'anon_chat_id' not in session:
        import uuid
        session['anon_chat_id'] = str(uuid.uuid4())

    return f"anon_{session['anon_chat_id']}"


def get_chat_history(user_id):
    """Получить историю чата для пользователя"""
    if user_id not in user_chats:
        user_chats[user_id] = [
            {
                "role": "assistant",
                "content": "Привет! Я ваш AI-ассистент по кулинарии. Могу помочь с рецептами, подсказать замену ингредиентов или дать совет по приготовлению. Чем могу помочь?"
            }
        ]
    return user_chats[user_id]


def save_chat_history(user_id, history):
    """Сохранить историю чата"""
    if len(history) > 20:
        history = history[-20:]

    user_chats[user_id] = history


def send_to_openrouter(message, user_id):
    """Отправить сообщение в OpenRouter API - С ПОДРОБНОЙ ОТЛАДКОЙ"""
    print(f"🔄 Отправка в OpenRouter: '{message}'")

    history = get_chat_history(user_id)

    # Проверка что history это список
    if not isinstance(history, list):
        print(f"⚠️ История не список! Исправляем...")
        history = [{"role": "assistant", "content": "История сброшена."}]

    # Добавляем сообщение пользователя
    history.append({"role": "user", "content": message})

    try:
        api_key = current_app.config.get('OPENROUTER_API_KEY')
        print(f"API ключ (первые 10 символов): {api_key[:10] if api_key else 'НЕТ'}...")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "meta-llama/llama-3.2-3b-instruct:free",
            "messages": [
                {"role": "system", "content": "Ты кулинарный помощник. Отвечай кратко по-русски."},
                {"role": "user", "content": message}
            ],
            "max_tokens": 300
        }

        print(f"Отправляю запрос к OpenRouter...")

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )

        print(f"Статус: {response.status_code}")
        print(f"Тип контента: {response.headers.get('Content-Type')}")
        print(f"Первые 200 символов ответа: {response.text[:200]}")

        # ПРОВЕРКА ЧТО ВЕРНУЛОСЬ
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"JSON успешно распарсен. Ключи: {data.keys()}")

                if 'choices' in data and len(data['choices']) > 0:
                    ai_response = data['choices'][0]['message']['content']
                    print(f"AI ответ: {ai_response[:100]}...")

                    # Добавляем ответ
                    history.append({"role": "assistant", "content": ai_response})
                    save_chat_history(user_id, history)

                    return ai_response, True
                else:
                    print(f"❌ Нет choices в ответе. Весь ответ: {data}")
                    raise ValueError("Нет choices в ответе API")

            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON. Ответ был: {response.text[:500]}")
                raise

        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"Полный ответ: {response.text}")
            raise Exception(f"HTTP ошибка {response.status_code}")

    except Exception as e:
        print(f"🚫 Исключение: {type(e).__name__}: {str(e)}")

        # ЛОКАЛЬНЫЙ ОТВЕТ ПРИ ЛЮБОЙ ОШИБКЕ
        local_response = get_local_response(message)
        print(f"Использую локальный ответ: {local_response[:50]}...")

        # СОХРАНЯЕМ В ИСТОРИЮ
        if isinstance(history, list):
            history.append({"role": "assistant", "content": local_response})
            save_chat_history(user_id, history)

        return local_response, False

def send_to_ai(message, user_id):
    """Отправка сообщения в AI (автоматически выбирает провайдера)"""
    # Сначала пробуем OpenRouter
    response, success = send_to_openrouter(message, user_id)

    if not success:
        # Если OpenRouter не сработал, пробуем локальные ответы
        response = get_local_response(message)
        save_chat_history(user_id, message)

    return response, success



def get_local_response(message):
    """Локальные ответы если API не работает"""
    message_lower = message.lower()

    responses = {
        "привет": "Привет! Я кулинарный помощник. Задайте вопрос о рецептах.",
        "рецепт": "Выберите категорию: Завтраки, Основные блюда, Десерты, Супы, Напитки.",
        "как приготовить": "Опишите блюдо, и я подскажу или найду похожий рецепт!",
        "аллерг": "В фильтрах можно исключить аллергены: орехи, молоко, глютен и др.",
        "вегетариан": "У нас есть вегетарианские рецепты! Выберите категорию.",
        "быстро": "Для быстрых рецептов посмотрите Завтраки или Основные блюда.",
        "десерт": "В категории Десерты найдете торты, пироги, печенье.",
        "суп": "В категории Супы есть различные первые блюда.",
        "напиток": "В категории Напитки найдете коктейли, чаи, кофейные рецепты.",
        "избранн": "Добавляйте рецепты в избранное сердечком ★",
        "спасибо": "Пожалуйста! Обращайтесь ещё 😊",
    }

    for key, answer in responses.items():
        if key in message_lower:
            return answer

    return f"""Я кулинарный помощник. Вы спросили: "{message}"\n\nПопробуйте:\n• Выбрать категорию рецептов\n• Использовать фильтры\n• Посмотреть избранное"""


def clear_chat_history(user_id):
    """Очистить историю чата"""
    user_chats[user_id] = [
        {
            "role": "assistant",
            "content": "История очищена. Чем могу помочь?"
        }
    ]