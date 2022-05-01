from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    paid_amount = Column(Float, nullable=False)

    # reference to all urls for the user
    urls = relationship("URL", back_populates="user", cascade="all,delete")


class URL(Base):
    __tablename__ = 'url'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    full_url = Column(String, nullable=False)
    alias = Column(String, nullable=False, unique=True)
    is_random = Column(Boolean, nullable=False, default=True)

    # reference to the user
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="urls")

    # reference to all urls for the user
    visitors = relationship("Visitor", back_populates="url", cascade="all,delete")


class Visitor(Base):
    __tablename__ = 'visitor'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    ip = Column(String, nullable=False)

    # reference to the url
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship("URL", back_populates="visitors")

    __table_args__ = (
        UniqueConstraint('ip', 'url_id', name='unique_idx_1'),
    )


models = [
    User,
    URL,
    Visitor
]
