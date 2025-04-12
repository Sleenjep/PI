from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Index
from pydantic import BaseModel

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    __table_args__ = (Index("ix_users_username", "username", unique=True),)

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)


class Token(BaseModel):
    access_token: str
    token_type: str
