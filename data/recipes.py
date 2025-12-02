import sqlalchemy
from sqlalchemy import orm

from .sqlalchemy_base import SqlAlchemyBase


class Recipes(SqlAlchemyBase):
    __tablename__ = 'recipes'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    ingredients = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    category = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    user = orm.relationship('User')
    allergens = orm.relationship('Allergen', secondary='recipe_allergen', backref='recipes')