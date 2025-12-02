from data import db_session
from data.default_allergens import DEFAULT_ALLERGENS
from data.allergens import Allergen


def add_new_allergens():
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()

    existing_titles = {a.title for a in db_sess.query(Allergen).all()}

    for allergen_name in DEFAULT_ALLERGENS:
        if allergen_name not in existing_titles:
            allergen = Allergen(title=allergen_name)
            db_sess.add(allergen)
            print(f"✅ Добавлен: {allergen_name}")

    db_sess.commit()
    print(f"\n🎉 Новые аллергены добавлены")


if __name__ == "__main__":
    add_new_allergens()