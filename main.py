from flask import Flask, render_template, redirect, request, abort, flash, jsonify
from data import db_session
from data.allergens import Allergen
from data.default_allergens import create_default_allergens
from data.recipes import Recipes
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.users import User
from forms.recipes import RecipesForm
from forms.user import RegisterForm, LoginForm
#from openai import OpenAI
from data.default_recipes import create_default_recipes
import os
from flask_htmx import HTMX
from sqlalchemy import or_, func, and_
import re
import requests
import json
from data.chat import get_user_id, get_chat_history, send_to_ai, clear_chat_history

# client = OpenAI(api_key="sk-2ac11b4f4b4142f8ae0e93bafe291802", base_url="https://api.deepseek.com")

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = '65432456uijhgfdsxcvbntghigfeloghlfgogug36364545464737re5dikkfuytotglbligjuftugitlgolgugtu'
@app.before_request
def force_guest_on_restart():
    from flask import session
    if 'initialized' not in session:
        session.clear()
        logout_user()
        session['initialized'] = True
login_manager = LoginManager()
login_manager.init_app(app)
htmx = HTMX(app)
app.config['DEEPSEEK_API_KEY'] = 'sk-9a1fadff540847dc9f98c343df501e25'
app.config['DEEPSEEK_API_URL'] = 'https://api.deepseek.com/chat/completions'
app.config['DEEPSEEK_MODEL'] = 'deepseek-chat'

@login_manager.user_loader
def load_user(user_id):
   db_sess = db_session.create_session()
   return db_sess.query(User).get(user_id)

db_session.global_init("db/blogs.db")
db_sess = db_session.create_session()
create_default_allergens(db_sess)
create_default_recipes(db_sess)
db_sess.close()

@app.route("/")
def index():
    THEME = os.environ.get('APP_THEME', 'food')

    if THEME == 'cosmic':
        template_name = 'index_cosmic.html'
    else:
        template_name = 'index.html'
    db_sess = db_session.create_session()
    categories = db_sess.query(Recipes.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    all_allergens = db_sess.query(Allergen).all()
    selected_category = request.args.get('category')
    recipes = []
    if selected_category:
        recipes = db_sess.query(Recipes).filter(Recipes.category == selected_category).all()
    return render_template(template_name, recipes=recipes, categories=categories, selected_category=selected_category, all_allergens=all_allergens, THEME=THEME)


@app.route("/search")
def search():
    """Простой поиск рецептов"""
    # Всегда используем отдельный шаблон для поиска
    template_name = 'searchres.html'

    db_sess = db_session.create_session()

    # Получаем параметры поиска
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    no_allergens = request.args.get('no_allergens') == 'true'

    # Базовый запрос
    recipes_query = db_sess.query(Recipes)

    # 1. Поиск по тексту
    if query:
        query_clean = query.strip()
        words = query_clean.split()

        # Если одно слово
        if len(words) == 1:
            pattern = f"%{query_clean}%"
            recipes_query = recipes_query.filter(
                or_(
                    Recipes.title.ilike(pattern),
                    Recipes.ingredients.ilike(pattern)
                )
            )

        # Если несколько слов
        else:
            # Ищем полную фразу
            full_pattern = f"%{query_clean}%"
            recipes_query = recipes_query.filter(
                or_(
                    Recipes.title.ilike(full_pattern),
                    Recipes.ingredients.ilike(full_pattern)
                )
            )

    # 2. Фильтр по категории
    if category:
        recipes_query = recipes_query.filter(Recipes.category == category)

    # 3. Фильтр без аллергенов
    if no_allergens:
        recipes_query = recipes_query.filter(~Recipes.allergens.any())

    # Получаем результаты
    all_recipes = recipes_query.all()

    # Получаем все категории для отображения
    categories = db_sess.query(Recipes.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]

    # Получаем все аллергены
    all_allergens = db_sess.query(Allergen).all()

    # Закрываем сессию
    db_sess.close()

    # Отображаем отдельный шаблон для поиска
    return render_template(template_name,
                           recipes=all_recipes,
                           categories=categories,
                           selected_category=category,
                           all_allergens=all_allergens,
                           search_query=query,
                           no_allergens_filter=no_allergens)
@app.route('/reqister', methods=['GET', 'POST'])
def reqister():
    """Регистрация (с опечаткой)"""
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                    form=form,
                                    message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                    form=form,
                                    message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/favourites')
@login_required
def favourites():
    db_sess = db_session.create_session()
    try:
        user = db_sess.query(User).get(current_user.id)
        favourite_recipes = user.favourite_recipes
        return render_template('favourites.html', recipes=favourite_recipes)
    finally:
        db_sess.close()

@app.route('/add_to_favourites/<int:recipe_id>')
@login_required
def add_to_favourites(recipe_id):
    db_sess = db_session.create_session()
    try:
        user = db_sess.query(User).get(current_user.id)
        recipe = db_sess.query(Recipes).get(recipe_id)
        if recipe and recipe not in user.favourite_recipes:
            user.favourite_recipes.append(recipe)
            db_sess.commit()
            flash('✅ Рецепт добавлен в избранное!', 'success')
    finally:
        db_sess.close()
    return redirect(request.referrer or '/')

@app.route('/remove_from_favourites/<int:recipe_id>')
@login_required
def remove_from_favourites(recipe_id):
    db_sess = db_session.create_session()
    try:
        user = db_sess.query(User).get(current_user.id)
        recipe = db_sess.query(Recipes).get(recipe_id)

        if recipe and recipe in user.favourite_recipes:
            user.favourite_recipes.remove(recipe)
            db_sess.commit()
            flash('❌ Рецепт удален из избранного', 'warning')
    finally:
        db_sess.close()
    return redirect(request.referrer or '/')

@app.route('/download_recipe/<int:recipe_id>')
def download_recipe(recipe_id):
    db_sess = db_session.create_session()
    recipe = db_sess.query(Recipes).get(recipe_id)

    if not recipe:
        return "Рецепт не найден", 404

    text = f"""
{recipe.title}
{'=' * 40}

Категория: {recipe.category}

Ингредиенты:
{recipe.ingredients}

Приготовление:
{recipe.content}

Аллергены: {', '.join([a.title for a in recipe.allergens])}
"""

    from io import BytesIO
    file = BytesIO(text.encode('utf-8'))

    db_sess.close()

    from flask import send_file
    return send_file(
        file,
        as_attachment=True,
        download_name=f'{recipe.title}.txt',
        mimetype='text/plain'
    )

#
# @app.route('/chat/send', methods=['POST'])
# def send_message():
#     """Отправить сообщение в AI"""
#     message = request.form.get('message', '').strip()
#
#     if not message:
#         return render_template('chat_message.html',
#                                message="Сообщение не может быть пустым",
#                                is_user=False)
#
#     user_id = get_user_id()
#
#     try:
#         # Используем чистую функцию DeepSeek
#         ai_response, success = send_to_ai(message, user_id)
#
#         if not success:
#             # Если ошибка в самой функции send_to_ai
#             return render_template('chat_message.html',
#                                    message=ai_response,  # Здесь уже сообщение об ошибке
#                                    is_user=False)
#
#         return render_template('chat_message.html',
#                                message=ai_response,
#                                is_user=False)
#
#     except Exception as e:
#         # Перехватываем исключения, которые могли не быть обработаны
#         error_msg = f"😔 Критическая ошибка: {str(e)}"
#         return render_template('chat_message.html',
#                                message=error_msg,
#                                is_user=False)
#
#
# @app.route('/chat/clear', methods=['POST'])
# def clear_chat():
#     """Очистить историю чата"""
#     user_id = get_user_id()
#     clear_chat_history(user_id)
#
#     return render_template('chat_message.html',
#                            message="История очищена. Чем могу помочь?",
#                            is_user=False)
#
#
# @app.route('/chat/history', methods=['GET'])
# def get_chat_history_route():
#     """Получить всю историю чата"""
#     user_id = get_user_id()
#     history = get_chat_history(user_id)
#
#     # Пропускаем первое приветственное сообщение
#     messages = history[1:] if len(history) > 1 else []
#
#     return render_template('chat_history.html', messages=messages)
#
# @app.route('/ai_chat')
# def ai_chat():
#     """Страница AI чата"""
#     return render_template('ai_chat.html')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')