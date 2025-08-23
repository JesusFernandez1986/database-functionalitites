import os
from sqla_wrapper import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean

db = SQLAlchemy(os.getenv("DATABASE_URL", "sqlite:///localhost.sqlite"))

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    secret_number = Column(String, unique=False)
    password = Column(String)
    session_token = Column(String)
    inactive = Column(Boolean, default=False)
