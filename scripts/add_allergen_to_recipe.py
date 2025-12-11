# add_allergen_to_recipe.py
from data import db_session
from data.recipes import Recipes
from data.allergens import Allergen


def add_allergen_to_recipe():
    db_session.global_init("../db/blogs.db")
    db_sess = db_session.create_session()

    # Настройки
    RECIPE_TITLE = "Суп Чаудер"  # ← замените на ваш рецепт
    ALLERGENS_TO_ADD = ["Треска"]  # ← аллергены для добавления

    recipe = db_sess.query(Recipes).filter(Recipes.title == RECIPE_TITLE).first()

    if not recipe:
        print(f"❌ Рецепт '{RECIPE_TITLE}' не найден")
        return

    print(f"📋 Текущие аллергены рецепта '{RECIPE_TITLE}':")
    for allergen in recipe.allergens:
        print(f"  - {allergen.title}")

    added_count = 0
    for allergen_name in ALLERGENS_TO_ADD:
        allergen = db_sess.query(Allergen).filter(Allergen.title == allergen_name).first()
        if allergen:
            if allergen not in recipe.allergens:
                recipe.allergens.append(allergen)
                added_count += 1
                print(f"✅ Добавлен: {allergen_name}")
            else:
                print(f"⏭️ Уже есть: {allergen_name}")
        else:
            print(f"❌ Аллерген не найден в БД: {allergen_name}")

    db_sess.commit()

    print(f"\n🎉 Добавлено новых аллергенов: {added_count}")
    print("📋 Итоговый список аллергенов:")
    for allergen in recipe.allergens:
        print(f"  - {allergen.title}")


if __name__ == "__main__":
    add_allergen_to_recipe()