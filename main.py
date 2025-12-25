from flask import Flask, render_template, redirect, request, abort, flash
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

# client = OpenAI(api_key="sk-2ac11b4f4b4142f8ae0e93bafe291802", base_url="https://api.deepseek.com")


app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = '65432456uijhgfdsxcvbntghigfeloghlfgogug36364545464737re5dikkfuytotglbligjuftugitlgolgugtu'
login_manager = LoginManager()
login_manager.init_app(app)



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
    # 1. Определение темы
    THEME = os.environ.get('APP_THEME', 'food')

    # 2. Выбор шаблона
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


@app.route('/register', methods=['GET', 'POST'])
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

# @app.route('/news',  methods=['GET', 'POST'])
# @login_required
# def add_news():
#     form = NewsForm()
#    if form.validate_on_submit():
#          db_sess = db_session.create_session()
#          news = Recipes()
#          news.title = form.title.data
#          news.content = form.content.data
#          news.is_private = form.is_private.data
#         current_user.news.append(news)
#         db_sess.merge(current_user)
#         db_sess.commit()
#         return redirect('/')
#     return render_template('news.html', title='Добавление новости',
#                            form=form)

# @app.route('/news/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit_news(id):
#     form = NewsForm()
#     if request.method == "GET":
#         db_sess = db_session.create_session()
#         news = db_sess.query(News).filter(News.id == id,
#                                           News.user == current_user
#                                           ).first()
#         if news:
#             form.title.data = news.title
#             form.content.data = news.content
#             form.is_private.data = news.is_private
#         else:
#             abort(404)
#     if form.validate_on_submit():
#         db_sess = db_session.create_session()
#         news = db_sess.query(News).filter(News.id == id,
#                                           News.user == current_user
#                                           ).first()
#         if news:
#             news.title = form.title.data
#             news.content = form.content.data
#             news.is_private = form.is_private.data
#             db_sess.commit()
#             return redirect('/')
#         else:
#             abort(404)
#     return render_template('news.html',
#                            title='Редактирование новости',
#                            form=form
#                            )
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

if __name__ == '__main__':
    app.run(port=8091, host='127.0.0.1')