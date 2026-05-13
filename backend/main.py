"""
财务造假识别系统 - FastAPI 后端入口
"""

import os
import json
import shutil
import tempfile
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models.schemas import FinancialStatement, AnalysisResult
from .analyzer.report import generate_report
from .analyzer.data_loader import load_financial_data, create_financial_statement
from .data.sample import get_sample_statement, generate_company_list

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="财务造假识别系统",
    description="基于 M-Score、Z-Score、多维财务比率和机器学习的财务造假检测系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== API 路由（优先匹配） =====
@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "财务造假识别系统 API"}


@app.post("/api/analyze/json", response_model=AnalysisResult)
async def analyze_from_json(statement: FinancialStatement):
    return generate_report(statement)


@app.post("/api/analyze/upload", response_model=AnalysisResult)
async def analyze_from_file(
    file: UploadFile = File(...),
    company_name: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
):
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        statement = load_financial_data(tmp_path)
        if company_name:
            statement.company_name = company_name
        if industry:
            statement.industry = industry
        result = generate_report(statement)
    finally:
        os.unlink(tmp_path)
    return result


@app.get("/api/samples")
async def list_samples():
    companies = generate_company_list()
    return [
        {
            "name": c.company_name,
            "industry": c.industry,
            "years": c.fiscal_years,
            "key": "normal" if "稳健" in c.company_name else "fraud",
        }
        for c in companies
    ]


@app.get("/api/sample/{name}", response_model=AnalysisResult)
async def analyze_sample(name: str = "normal"):
    statement = get_sample_statement(name)
    return generate_report(statement)


# ===== 前端静态文件（最后匹配） =====
if FRONTEND_DIR.exists():
    # 静态资源 (CSS/JS)
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
