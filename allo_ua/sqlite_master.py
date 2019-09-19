import json

from sqlalchemy import create_engine, Column, String, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

engine = create_engine('sqlite:///allo_ua.db', echo=False, poolclass=QueuePool)
_SessionFactory = sessionmaker(bind=engine)

Base = declarative_base()


def session_factory():
    Base.metadata.create_all(engine)
    return _SessionFactory()


class AlloUaTips(Base):
    __tablename__ = 'allo_ua_tips'

    id = Column(Integer, primary_key=True)
    request = Column(String(3), unique=True)
    response_query = Column(Text)
    response_products = Column(Text)
    response_categories = Column(Text)
    complete = Column(Boolean)

    def __init__(self, request, query, products, categories, complete=False):
        self.request = request
        self.response_query = json.dumps(query, ensure_ascii=False)
        self.response_products = json.dumps(products, ensure_ascii=False)
        self.response_categories = json.dumps(categories, ensure_ascii=False)
        self.complete = complete
