from sqlalchemy import Column, String, ForeignKey
from app.models.base import Base

class Category(Base):
    __tablename__ = "category"
    category_id = Column(String(16), primary_key=True, index=True)
    category_name = Column(String(100), nullable=True)
    company_id = Column(String(16), ForeignKey("company.company_id"), nullable=True)
    client_id = Column(String(16), ForeignKey("client.client_id"), nullable=True)