import os
import json
import pandas as pd
from datetime import datetime
from typing import Union

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.base import SessionLocal
from app.models import company as company_model
from app.models import category as category_model
from app.models import transaction as transaction_model
from app.utils.parser import save_upload_file_tmp


def save_upload_file_tmp(upload_file: UploadFile) -> str:
    import tempfile
    suffix = os.path.splitext(upload_file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload_file.file.read())
        return tmp.name

async def process_transactions(
    bank_file: Union[UploadFile, str],
    rule_file: Union[UploadFile, str]
) -> dict:

    if isinstance(bank_file, UploadFile):
        bank_path = save_upload_file_tmp(bank_file)
    else:
        bank_path = bank_file

    if isinstance(rule_file, UploadFile):
        rule_path = save_upload_file_tmp(rule_file)
    else:
        rule_path = rule_file

    df = pd.read_csv(bank_path)
    with open(rule_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    db: Session = SessionLocal()
    total = len(df)
    processed = 0
    unmatched = 0
    classified_list = []
    unclassified_list = []

    for comp in rules["companies"]:
        company = db.query(company_model.Company).filter_by(company_id=comp["company_id"]).first()
        if not company:
            company = company_model.Company(
                company_id=comp["company_id"],
                company_name=comp["company_name"]
            )
            db.add(company)
        for cat in comp["categories"]:
            category = db.query(category_model.Category).filter_by(category_id=cat["category_id"]).first()
            if not category:
                category = category_model.Category(
                    category_id=cat["category_id"],
                    category_name=cat["category_name"],
                    company_id=comp["company_id"]
                )
                db.add(category)
    db.commit()

    for idx, row in df.iterrows():
        desc = str(row.get("적요", ""))
        거래일시 = row.get("거래일시")
        입금액 = int(row.get("입금액", 0) or 0)
        출금액 = int(row.get("출금액", 0) or 0)
        거래후잔액 = int(row.get("거래후잔액", 0) or 0)
        now_str = datetime.now().strftime("%Y%m%d%H%M%S")

        matched = False
        classified_company_id = None
        classified_category_id = None
        classified_category_name = None

        for comp in rules["companies"]:
            for cat in comp["categories"]:
                for keyword in cat["keywords"]:
                    if keyword in desc:
                        t = transaction_model.Transaction(
                            transaction_date=거래일시,
                            company_id=comp["company_id"],
                            category_id=cat["category_id"],
                            deposit=입금액,
                            withdrawal=출금액,
                            balance=거래후잔액,
                            description=desc,
                            raw=json.dumps(row.to_dict(), ensure_ascii=False),
                            is_matched="Y",
                            create_date=now_str,
                            create_by="SYSTEM",
                            update_date=now_str,
                            update_by="SYSTEM"
                        )
                        db.add(t)
                        processed += 1
                        matched = True
                        classified_company_id = comp["company_id"]
                        classified_category_id = cat["category_id"]
                        classified_category_name = cat["category_name"]
                        break
                if matched:
                    break
            if matched:
                break

        result_dict = {
            "거래일시": 거래일시,
            "회사번호": classified_company_id,
            "카테고리번호": classified_category_id,
            "카테고리명": classified_category_name,
            "적요": desc,
            "입금액": 입금액,
            "출금액": 출금액,
            "거래후잔액": 거래후잔액,
            "분류여부": "Y" if matched else "N",
            "생성일시": now_str,
            "생성자": "SYSTEM",
            "수정일시": now_str,
            "수정자": "SYSTEM"
        }

        if matched:
            classified_list.append(result_dict)
        else:
            t = transaction_model.Transaction(
                transaction_date=거래일시,
                company_id=None,
                category_id=None,
                deposit=입금액,
                withdrawal=출금액,
                balance=거래후잔액,
                description=desc,
                raw=json.dumps(row.to_dict(), ensure_ascii=False),
                is_matched="N",
                create_date=now_str,
                create_by="SYSTEM",
                update_date=now_str,
                update_by="SYSTEM"
            )
            db.add(t)
            unmatched += 1
            unclassified_list.append(result_dict)

    db.commit()
    db.close()
    return {
        "전체건수": total,
        "분류건수": processed,
        "미분류건수": unmatched,
        "메시지": f"{processed}건 분류 완료, {unmatched}건 미분류",
        "저장데이터": {
            "분류목록": classified_list,
            "미분류목록": unclassified_list
        }
    }