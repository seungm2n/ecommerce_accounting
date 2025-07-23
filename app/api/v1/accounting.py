from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from app.services.accounting_service import (
    process_transactions,
    get_records,
)
from typing import Any, Optional
import os

router = APIRouter()


@router.post("/process")
async def process_accounting(
    bank_file: Optional[UploadFile] = File(None),
    rule_file: Optional[UploadFile] = File(None)
) -> Any:
    try:
        # 파일이 없으면 기본 경로로 대체
        if bank_file is None:
            bank_file = "./data/bank_transactions.csv"
        if rule_file is None:
            rule_file = "./data/rules.json"

        result = await process_transactions(bank_file, rule_file)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records")
async def get_accounting_records(companyId: str = Query(...)) -> Any:
    try:
        records = await get_records(companyId)
        return records
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
