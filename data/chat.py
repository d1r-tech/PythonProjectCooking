import requests
import json
from flask import current_app, session
import time

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
    if len(history) > 30:  # Ограничиваем историю 30 сообщениями
        # Сохраняем первое системное сообщение и последние 29
        if history[0]["role"] == "assistant":
            history = [history[0]] + history[-29:]
        else:
            history = history[-30:]

    user_chats[user_id] = history


def send_to_deepseek(message, user_id):
    """Отправить сообщение в DeepSeek API - чистая реализация"""
    print(f"🔄 Отправка в DeepSeek: '{message}'")

    # Получаем историю
    history = get_chat_history(user_id)

    # Добавляем сообщение пользователя в историю
    history.append({"role": "user", "content": message})

    try:
        # Получаем конфигурацию из приложения
        api_key = current_app.config.get('DEEPSEEK_API_KEY')
        api_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/chat/completions')
        model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat')

        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY не настроен")

        print(f"Использую модель: {model}")

        # Подготовка заголовков
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Системный промпт для кулинарного помощника
        system_prompt = """Ты - AI-ассистент кулинарного приложения FoodHub.
Твоя специализация:
1. Рецепты и приготовление блюд
2. Замена ингредиентов 
3. Советы по кулинарной технике
4. Хранение продуктов
5. Ответы на вопросы о питании

Правила:
- Отвечай кратко и по делу
- Будь дружелюбным и полезным
- Если вопрос не по теме, вежливо откажись
- Форматируй ответы для удобного чтения
- Используй эмодзи для лучшей наглядности

Контекст приложения:
- У пользователей есть фильтры по аллергенам
- Есть категории: Завтраки, Основные блюда, Десерты, Супы, Напитки
- Пользователи могут добавлять рецепты в избранное"""

        # Формируем сообщения для API
        messages_for_api = [
            {"role": "system", "content": system_prompt}
        ]

        # Добавляем историю (последние 15 сообщений для экономии токенов)
        for msg in history[-15:]:
            messages_for_api.append(msg)

        # Подготовка тела запроса
        payload = {
            "model": model,
            "messages": messages_for_api,
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }

        print(f"Отправляю запрос к DeepSeek API...")

        # Отправка запроса с таймаутом
        start_time = time.time()
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=45  # Увеличиваем таймаут
        )
        response_time = time.time() - start_time
        print(f"Время ответа: {response_time:.2f} сек")

        # Проверка статуса
        if response.status_code == 200:
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                ai_response = data['choices'][0]['message']['content']

                # Логирование успеха
                print(f"✅ Успешный ответ от DeepSeek")
                print(f"Использовано токенов: {data.get('usage', {}).get('total_tokens', 'неизвестно')}")

                # Добавляем ответ ассистента в историю
                history.append({"role": "assistant", "content": ai_response})
                save_chat_history(user_id, history)

                return ai_response, True
            else:
                print(f"❌ Некорректный ответ от API: {data}")
                raise ValueError("Нет choices в ответе API")

        elif response.status_code == 401:
            print(f"❌ Ошибка аутентификации: неверный API ключ")
            raise PermissionError("Неверный API ключ DeepSeek")

        elif response.status_code == 429:
            print(f"❌ Слишком много запросов")
            raise Exception("Превышен лимит запросов. Попробуйте позже.")

        elif response.status_code == 500:
            print(f"❌ Ошибка сервера DeepSeek")
            raise Exception("Временная ошибка сервера DeepSeek")

        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            raise Exception(f"Ошибка API: {response.status_code}")

    except requests.exceptions.Timeout:
        print(f"🚫 Таймаут запроса к DeepSeek (более 45 секунд)")
        raise Exception("Время ожидания истекло. Попробуйте еще раз.")

    except requests.exceptions.ConnectionError:
        print(f"🚫 Ошибка подключения к DeepSeek")
        raise Exception("Ошибка подключения к серверу.")

    except Exception as e:
        print(f"🚫 Неожиданная ошибка: {type(e).__name__}: {str(e)}")
        raise


def send_to_ai(message, user_id):
    """Отправка сообщения в AI - только DeepSeek"""
    try:
        response, success = send_to_deepseek(message, user_id)
        if success:
            return response, True
        else:
            raise Exception("DeepSeek вернул неуспешный статус")
    except Exception as e:
        # Возвращаем понятное сообщение об ошибке
        error_message = f"😔 Извините, произошла ошибка при обращении к AI: {str(e)}"

        # Добавляем сообщение об ошибке в историю
        history = get_chat_history(user_id)
        history.append({"role": "assistant", "content": error_message})
        save_chat_history(user_id, history)

        return error_message, False


def clear_chat_history(user_id):
    """Очистить историю чата"""
    user_chats[user_id] = [
        {
            "role": "assistant",
            "content": "История очищена. Чем могу помочь?"
        }
    ]