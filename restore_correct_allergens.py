from data import db_session
from data.recipes import Recipes
from data.allergens import Allergen


def restore_correct_allergens():
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()

    # ПРАВИЛЬНЫЕ АЛЛЕРГЕНЫ ДЛЯ КАЖДОГО РЕЦЕПТА
    CORRECT_ALLERGENS = {
        "Овсяная каша": ["Глютен", "Молоко"],
        "Манная каша": ["Глютен", "Молоко"],
        "Сырники": ["Яйца", "Молоко", "Глютен"],
        "Блины": ["Глютен", "Молоко", "Яйца"],
        "Суп Чаудер": ["Глютен", "Молоко", "Картофель", "Треска"],
        "Куриный суп с лапшой": ["Глютен", "Картофель", "Морковь"]
    }

    for recipe_title, allergens_list in CORRECT_ALLERGENS.items():
        recipe = db_sess.query(Recipes).filter(Recipes.title == recipe_title).first()
        if recipe:
            # Очищаем и устанавливаем правильные
            recipe.allergens.clear()

            added = []
            for allergen_name in allergens_list:
                allergen = db_sess.query(Allergen).filter(Allergen.title == allergen_name).first()
                if allergen:
                    recipe.allergens.append(allergen)
                    added.append(allergen_name)
                else:
                    print(f"⚠️ Аллерген не найден: {allergen_name}")

            print(f"✅ {recipe_title}: {', '.join(added)}")

    db_sess.commit()
    print("\n🎉 Все аллергены восстановлены!")


if __name__ == "__main__":
    restore_correct_allergens()