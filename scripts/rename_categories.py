# rename_categories.py
from data import db_session
from data.recipes import Recipes


def rename_categories():
    db_session.global_init("../db/blogs.db")
    db_sess = db_session.create_session()

    # СТАРОЕ название → НОВОЕ название
    CATEGORY_MAP = {
        "Завтраки": "Утренние планеты 🪐",
        "Супы": "Гравитационные супы 🥣",
        "Десерты": "Сладкие созвездия ✨",
        "Основные блюда": "Орбитальные обеды🛰️🥘"
    }

    try:
        changed_count = 0

        for old_name, new_name in CATEGORY_MAP.items():
            # Находим все рецепты со старой категорией
            recipes = db_sess.query(Recipes).filter(
                Recipes.category == old_name
            ).all()

            if recipes:
                for recipe in recipes:
                    recipe.category = new_name
                changed_count += len(recipes)
                print(f"✅ '{old_name}' → '{new_name}': {len(recipes)} рецептов")
            else:
                print(f"ℹ️ Рецептов в категории '{old_name}' не найдено")

        if changed_count > 0:
            db_sess.commit()
            print(f"\n🎉 Переименовано: {changed_count} рецептов")
            print("Запустите приложение для проверки!")
        else:
            print("🤷 Ничего не изменилось")

    except Exception as e:
        db_sess.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        db_sess.close()


if __name__ == "__main__":
    rename_categories()