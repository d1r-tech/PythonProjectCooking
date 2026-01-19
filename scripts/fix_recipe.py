from data import db_session
from data.recipes import Recipes
from data.allergens import Allergen


def fix_recipe():
    db_session.global_init("../db/blogs.db")
    db_sess = db_session.create_session()
    try:
        recipe = db_sess.query(Recipes).filter(
            Recipes.title == "Глазунья"
        ).first()

        if not recipe:
            print("Рецепт не найден")
            return

        print(f"Исправляем рецепт: {recipe.title}")

        recipe.category = "Утренние планеты 🪐"
        print(f"Категория изменена на: {recipe.category}")

        recipe.allergens.clear()

        correct_allergens = ["Яйца", "Молоко", "Глютен"]

        for allergen_name in correct_allergens:
            allergen = db_sess.query(Allergen).filter(
                Allergen.title == allergen_name
            ).first()

            if allergen:
                recipe.allergens.append(allergen)
                print(f"Добавлен аллерген: {allergen.title}")
            else:
                print(f"Аллерген не найден в БД: {allergen_name}")

        db_sess.commit()
        print("Рецепт исправлен!")

    except Exception as e:
        db_sess.rollback()
        print(f"Ошибка: {e}")
    finally:
        db_sess.close()


if __name__ == "__main__":
    fix_recipe()