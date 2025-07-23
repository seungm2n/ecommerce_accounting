import tempfile
import shutil
from fastapi import UploadFile

def save_upload_file_tmp(upload_file: UploadFile) -> str:
    suffix = "." + upload_file.filename.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(upload_file.file, tmp)
        return tmp.name