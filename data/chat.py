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
    """Отправить сообщение в DeepSeek API"""
    history = get_chat_history(user_id)

    history.append({"role": "user", "content": message})

    try:
        headers = {
            "Authorization": f"Bearer {current_app.config['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json"
        }

        recent_history = history[-10:] if len(history) > 10 else history

        payload = {
            "model": "deepseek-chat",
            "messages": recent_history,
            "stream": False,
            "max_tokens": 1000,
            "temperature": 0.7
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

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