from sqlalchemy import Column, String, Integer, ARRAY, BigInteger

from app.database import Base


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    location  = Column(String, nullable=False)
    language = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    subjects = Column(ARRAY(String), nullable=False)