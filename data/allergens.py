import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, String, Table

from .sqlalchemy_base import SqlAlchemyBase

recipe_allergen = Table(
    'recipe_allergen',
    SqlAlchemyBase.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id')),
    Column('allergen_id', Integer, ForeignKey('allergens.id'))
)

class Allergen(SqlAlchemyBase):
    __tablename__ = 'allergens'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)

