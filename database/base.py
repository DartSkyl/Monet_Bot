import datetime

from sqlalchemy import Column, INTEGER, VARCHAR, DATE
from sqlalchemy.orm import declarative_base
import asyncpg as apg

MainBotModel = declarative_base()
conn = apg.connect()


class UsersInOpenGroup(MainBotModel):
    """Таблицв содержит пользователей из открытой группы"""
    __tablename__ = 'users_in_open_group'
    # Telegram user ID
    user_id = Column(INTEGER, primary_key=True, nullable=False)
    # Telegram user full name
    full_name = Column(VARCHAR, nullable=True)
    # User registration date
    reg_date = Column(DATE, default=datetime.date.today())


class TrailSubscription(MainBotModel):
    __tablename__ = 'trail_subscription'
    user_id = Column(INTEGER, primary_key=True, nullable=False)
    activation_date = Column(DATE, default=datetime.date.today())
