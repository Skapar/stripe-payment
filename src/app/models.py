from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Table
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False)
    paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Task(Base):
    __table__ = Table(
        'tasks', Base.metadata, 
        Column('task_id', String(36), primary_key=True),
        Column('status', String(20), nullable=False),
        Column('result', JSON, nullable=True)
    )

    def __repr__(self):
        return f"<Task {self.task_id}>"

class CheckoutRequest(BaseModel):
    price: int
    currency: str = "usd"
    success_url: str
    cancel_url: str