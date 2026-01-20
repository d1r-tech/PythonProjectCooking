#from .allergens import Allergen

DEFAULT_ALLERGENS = [
    "Молоко",
    "Яйца",
    "Пшеница",
    "Соя",
    "Лосось",
    "Треска",
    "Креветки",
    "Крабовые палочки",
    "Мидии",
    "Скумбрия",
    "Сельдь",
    "Кальмар",
    "Икра",
    "Киви",
    "Банан",
    "Авокадо",
    "Яблоко",
    "Помидор",
    "Клубника",
    "Апельсин",
    "Лимон",
    "Ананас",
    "Чеснок",
    "Мята",
    "Тыква",
    "Глютен",
    "Мед",
    "Морковь",
    "Картофель",
    "Миндаль",
    "Фисташка",
    "Кешью",
    "Арахис",
    "Абрикос",
    "Виноград",
    "Грецкий орех",
    "Белая рыба"
]

def create_default_allergens(db_sess):
    from .allergens import Allergen
    db_sess.query(Allergen).delete()
    for allergen_title in DEFAULT_ALLERGENS:
        if allergen_title and allergen_title.strip():
            allergen = Allergen(title=allergen_title.strip())
            db_sess.add(allergen)
    db_sess.commit()
