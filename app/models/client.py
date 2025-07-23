from sqlalchemy import Column, String
from app.models.base import Base

class Client(Base):
    __tablename__ = "client"
    client_id = Column(String, primary_key=True, index=True)
    client_name = Column(String, nullable=True)