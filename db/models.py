from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    paid_amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # reference to all urls for the user
    urls = relationship("URL", back_populates="user", cascade="all,delete")


class URL(Base):
    __tablename__ = 'url'
    id = Column(Integer, primary_key=True)
    fullurl = Column(String, nullable=False)
    alias = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # reference to the user
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="urls")


models = [
    User,
    URL,
]
