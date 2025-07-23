from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from datetime import datetime
from app.models.base import Base

class Transaction(Base):
    __tablename__ = "transaction"
    transaction_id = Column(Integer, primary_key=True, index=True)
    transaction_date = Column(String, nullable=True)
    client_id = Column(String, ForeignKey("client.client_id"), nullable=True)  # [★필수] 고객사ID 추가!
    company_id = Column(String, ForeignKey("company.company_id"), nullable=True)
    category_id = Column(String, ForeignKey("category.category_id"), nullable=True)
    deposit = Column(Integer)
    withdrawal = Column(Integer)
    balance = Column(Integer)
    description = Column(String)
    is_matched = Column(String(1), default='N')
    create_date = Column(String, nullable=True)
    create_by = Column(String, nullable=True, default="SYSTEM")
    update_date = Column(String, nullable=True)
    update_by = Column(String, nullable=True, default="SYSTEM")
    raw = Column(Text)