from flask import Flask, render_template, redirect, request, abort, flash, jsonify
from data import db_session
from data.allergens import Allergen
from data.default_allergens import create_default_allergens
from data.recipes import Recipes
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.users import User
from forms.recipes import RecipesForm
from forms.user import RegisterForm, LoginForm
from data.default_recipes import create_default_recipes
import os
from flask_htmx import HTMX
from sqlalchemy import or_, func, and_


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
    db_sess = db_session.create_session()

    query = request.args.get('q', '').strip().lower()
    print(f"🔍 Python поиск (AND логика): '{query}'")

    all_recipes = db_sess.query(Recipes).all()

    if not query:
        recipes = all_recipes
    else:
        recipes = []
        words = [w for w in query.split() if w]

        for recipe in all_recipes:
            title_lower = recipe.title.lower()

            all_words_found = True

            for word in words:
                if word in title_lower:
                    continue
                else:
                    all_words_found = False
                    break

            if all_words_found:
                recipes.append(recipe)
    for recipe in recipes:
        _ = recipe.allergens

    print(f"ИТОГ: Найдено {len(recipes)} рецептов")
    categories = db_sess.query(Recipes.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    all_allergens = db_sess.query(Allergen).all()

    db_sess.close()

    return render_template('searchres.html',
                           recipes=recipes,
                           search_query=query,
                           categories=[],
                           all_allergens=[])

@app.route('/reqister', methods=['GET', 'POST'])
def reqister():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0')