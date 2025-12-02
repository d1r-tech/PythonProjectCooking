import sqlalchemy
from sqlalchemy import orm
from .sqlalchemy_base import SqlAlchemyBase

favourite_recipes = sqlalchemy.Table(
    'favourites',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('recipe_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('recipes.id'))
)