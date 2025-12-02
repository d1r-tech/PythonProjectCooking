from data import db_session
from data.recipes import Recipes
from data.allergens import Allergen


def update_recipes():
    """Добавляет только новые рецепты из default_recipes.py в БД"""
    from data.default_recipes import DEFAULT_RECIPES  # ← импорт ВНУТРИ функции

    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()

    # Получаем существующие названия рецептов
    existing_titles = [r.title for r in db_sess.query(Recipes).all()]
    print(f"📊 Рецептов уже в БД: {len(existing_titles)}")

    added_count = 0
    for recipe_data in DEFAULT_RECIPES:
        if recipe_data["title"] not in existing_titles:
            # Создаем новый рецепт
            recipe = Recipes()
            recipe.title = recipe_data["title"]
            recipe.ingredients = recipe_data["ingredients"]
            recipe.content = recipe_data["content"]
            recipe.category = recipe_data["category"]

            # Добавляем аллергены
            allergen_count = 0
            for allergen_name in recipe_data["allergens"]:
                allergen = db_sess.query(Allergen).filter(Allergen.title == allergen_name).first()
                if allergen:
                    recipe.allergens.append(allergen)
                    allergen_count += 1

            db_sess.add(recipe)
            added_count += 1
            print(f"✅ Добавлен: {recipe.title} (аллергенов: {allergen_count})")
        else:
            print(f"⏭️ Уже есть: {recipe_data['title']}")

    db_sess.commit()
    db_sess.close()

    print(f"\n🎉 Добавлено новых рецептов: {added_count}")
    print(f"📊 Всего рецептов в БД: {len(existing_titles) + added_count}")


if __name__ == "__main__":
    update_recipes()