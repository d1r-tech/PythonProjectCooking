from data import db_session
from data.recipes import Recipes

db_session.global_init("db/blogs.db")
db_sess = db_session.create_session()

count = db_sess.query(Recipes).count()
print(f"Всего рецептов в БД: {count}")

recipes = db_sess.query(Recipes).limit(5).all()
for i, recipe in enumerate(recipes, 1):
    print(f"{i}. {recipe.title} (ID: {recipe.id})")

if recipes:
    first = recipes[0]
    print(f"\nПроверка поля theme у первого рецепта:")
    print(f"   Название: {first.title}")
    print(f"   Есть ли theme?: {hasattr(first, 'theme')}")
    if hasattr(first, 'theme'):
        print(f"   Значение theme: {first.theme}")