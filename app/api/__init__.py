from app.models.base import engine, Base
from app.models.client import Client
from app.models.company import Company
from app.models.category import Category
from app.models.transaction import Transaction

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("DB 테이블 초기화 완료!")