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


def send_to_deepseek(message, user_id):
    """Отправить сообщение в DeepSeek API - с улучшенной обработкой ошибок"""
    print(f"🔄 Отправка в DeepSeek: '{message[:50]}...'")

    history = get_chat_history(user_id)
    history.append({"role": "user", "content": message})

    try:
        headers = {
            "Authorization": f"Bearer {current_app.config['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json"
        }

        # Упрощенный payload
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful cooking assistant."},
                {"role": "user", "content": message}
            ],
            "max_tokens": 500
        }

        print(f"Отправляю запрос на DeepSeek API...")
        print(f"Headers: {headers}")
        print(f"Payload keys: {payload.keys()}")

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"Статус ответа: {response.status_code}")
        print(f"Заголовки ответа: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"Ответ получен, структура: {data.keys()}")

            ai_response = data['choices'][0]['message']['content']
            print(f"AI ответ (первые 100 символов): {ai_response[:100]}...")

            history.append({"role": "assistant", "content": ai_response})
            save_chat_history(user_id, history)

            return ai_response, True

        elif response.status_code == 402:
            error_msg = "⚠️ Ошибка оплаты API. Проверьте баланс на platform.deepseek.com"
            print(error_msg)

        elif response.status_code == 401:
            error_msg = "🔑 Неверный API ключ. Проверьте ключ на platform.deepseek.com"
            print(error_msg)

        elif response.status_code == 429:
            error_msg = "⏰ Лимит запросов превышен. Подождите немного."
            print(error_msg)

        else:
            error_msg = f"❌ Ошибка API {response.status_code}: {response.text[:200]}"
            print(error_msg)

        # Фолбэк ответ
        fallback_response = f"""
        Технические трудности с AI ассистентом (ошибка {response.status_code}).<br><br>

        <strong>Что вы можете сделать:</strong><br>
        1. Проверить баланс на <a href="https://platform.deepseek.com" target="_blank">platform.deepseek.com</a><br>
        2. Попробовать позже<br>
        3. Использовать поиск по рецептам на сайте<br><br>

        <em>А пока вот ответ на ваше сообщение "{message}":<br>
        Попробуйте поискать рецепт в нашей базе данных!</em>
        """

        history.append({"role": "assistant", "content": fallback_response})
        save_chat_history(user_id, history)

        return fallback_response, False

    except Exception as e:
        error_msg = f"🚫 Исключение: {type(e).__name__}: {str(e)}"
        print(error_msg)

        fallback_response = f"""
        Техническая ошибка подключения.<br><br>

        <strong>Что вы написали:</strong> "{message}"<br><br>

        <em>Пока AI ассистент настраивается, вы можете:</em><br>
        • Использовать поиск по категориям<br>
        • Посмотреть избранные рецепты<br>
        • Попробовать позже
        """

        return fallback_response, False
        if response.status_code == 200:
            data = response.json()
            ai_response = data['choices'][0]['message']['content']

            history.append({"role": "assistant", "content": ai_response})
            save_chat_history(user_id, history)

            return ai_response, True
        else:
            error_msg = f"Ошибка API: {response.status_code}"
            history.append({"role": "assistant", "content": error_msg})
            save_chat_history(user_id, history)
            return error_msg, False

    except Exception as e:
        error_msg = f"Ошибка соединения: {str(e)}"
        history.append({"role": "assistant", "content": error_msg})
        save_chat_history(user_id, history)
        return error_msg, False


def clear_chat_history(user_id):
    """Очистить историю чата"""
    user_chats[user_id] = [
        {
            "role": "assistant",
            "content": "История очищена. Чем могу помочь?"
        }
    ]