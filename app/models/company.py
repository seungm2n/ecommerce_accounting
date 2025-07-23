from sqlalchemy import Column, String, ForeignKey
from app.models.base import Base

class Company(Base):
    __tablename__ = "company"
    company_id = Column(String(16), primary_key=True, index=True)
    company_name = Column(String(100), nullable=True)
    client_id = Column(String(16), ForeignKey("client.client_id"), nullable=True)