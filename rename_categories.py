# rename_categories.py
from data import db_session
from data.recipes import Recipes

print("🔄 Переименовываем категории в БД...")

db_session.global_init("db/blogs.db")
db_sess = db_session.create_session()

# Маппинг: Космические → Обычные
RENAME_MAP = {
    'Утренние планеты 🪐': 'Завтраки',
    'Основные блюда 🍛': 'Основные блюда',  # убираем только эмодзи
    'Сладкие созвездия ✨': 'Десерты',
    'Гравитационные супы 🥣': 'Супы',
    'Галактические напитки 🚀': 'Напитки',
}

# Переименовываем ВСЕ рецепты
updated = 0
recipes = db_sess.query(Recipes).all()

for recipe in recipes:
    if recipe.category in RENAME_MAP:
        old = recipe.category
        recipe.category = RENAME_MAP[old]
        updated += 1
        print(f"  {old} → {recipe.category}")

db_sess.commit()
print(f"\n✅ Переименовано рецептов: {updated}")
print("🎉 БД теперь содержит обычные названия категорий!")

# Проверка
categories = db_sess.query(Recipes.category).distinct().all()
print("\n📋 Новые категории в БД:")
for cat in categories:
    print(f"  - {cat[0]}")