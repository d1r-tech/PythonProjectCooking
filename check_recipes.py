from data import db_session
from data.recipes import Recipes

db_session.global_init("db/blogs.db")
db_sess = db_session.create_session()

# 1. Сколько всего рецептов?
count = db_sess.query(Recipes).count()
print(f"📊 Всего рецептов в БД: {count}")

# 2. Покажем первые 5
recipes = db_sess.query(Recipes).limit(5).all()
for i, recipe in enumerate(recipes, 1):
    print(f"{i}. {recipe.title} (ID: {recipe.id})")

# 3. Проверим есть ли поле theme
if recipes:
    first = recipes[0]
    print(f"\n🔍 Проверка поля theme у первого рецепта:")
    print(f"   Название: {first.title}")
    print(f"   Есть ли theme?: {hasattr(first, 'theme')}")
    if hasattr(first, 'theme'):
        print(f"   Значение theme: {first.theme}")