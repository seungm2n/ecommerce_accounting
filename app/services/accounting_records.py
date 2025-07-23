from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models import category as category_model
from app.models import transaction as transaction_model

async def get_records(company_id: str):
    db: Session = SessionLocal()
    transactions = (
        db.query(transaction_model.Transaction)
        .filter(transaction_model.Transaction.company_id == company_id)
        .all()
    )
    results = []
    for t in transactions:
        category = None
        if t.category_id:
            category = db.query(category_model.Category).filter_by(category_id=t.category_id).first()
        results.append({
            "거래번호": t.transaction_id,
            "거래일시": t.transaction_date,
            "회사번호": t.company_id,
            "카테고리번호": t.category_id,
            "카테고리명": category.category_name if category else None,
            "적요": t.description,
            "입금액": t.deposit,
            "출금액": t.withdrawal,
            "거래후잔액": t.balance,
            "분류여부": t.is_matched,
            "생성일시": t.create_date,
            "생성자": t.create_by,
            "수정일시": t.update_date,
            "수정자": t.update_by,
        })
    db.close()
    return results