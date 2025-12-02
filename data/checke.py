# check_allergens_exist.py
from data import db_session
from data.allergens import Allergen

db_session.global_init("db/blogs.db")
db_sess = db_session.create_session()

needed_allergens = ["Яйца", "Морковь", "Картофель"]
print("=== ПРОВЕРКА АЛЛЕРГЕНОВ ===")

for allergen_name in needed_allergens:
    allergen = db_sess.query(Allergen).filter(Allergen.title == allergen_name).first()
    if allergen:
        print(f"✅ {allergen_name} - есть в БД")
    else:
        print(f"❌ {allergen_name} - НЕТ в БД! Добавьте в default_allergens.py")