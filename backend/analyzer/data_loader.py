"""
数据加载器：支持 CSV、Excel 和 JSON 格式的财务数据导入。
支持中英文列名自动映射。
"""

from typing import Optional
import pandas as pd
import numpy as np
from ..models.schemas import FinancialData, FinancialStatement


# 中英文列名映射
COLUMN_MAP = {
    # 损益表
    "营业收入": "revenue",
    "营业总收入": "revenue",
    "revenue": "revenue",
    "net sales": "revenue",
    "营业成本": "cost_of_revenue",
    "cost of revenue": "cost_of_revenue",
    "cost_of_revenue": "cost_of_revenue",
    "毛利": "gross_profit",
    "gross profit": "gross_profit",
    "gross_profit": "gross_profit",
    "销售管理费用": "sg_and_a",
    "销售、一般及管理费用": "sg_and_a",
    "sg&a": "sg_and_a",
    "sg_and_a": "sg_and_a",
    "折旧摊销": "depreciation",
    "折旧与摊销": "depreciation",
    "depreciation": "depreciation",
    "净利润": "net_income",
    "归母净利润": "net_income",
    "net income": "net_income",
    "net_income": "net_income",
    "利息支出": "interest_expense",
    "interest expense": "interest_expense",
    "interest_expense": "interest_expense",
    "所得税": "income_tax",
    "income tax": "income_tax",
    "income_tax": "income_tax",
    "息税前利润": "ebit",
    "ebit": "ebit",
    "经营活动现金流": "operating_cash_flow",
    "经营活动现金流量净额": "operating_cash_flow",
    "operating cash flow": "operating_cash_flow",
    "operating_cash_flow": "operating_cash_flow",
    # 资产负债表
    "总资产": "total_assets",
    "资产总计": "total_assets",
    "total assets": "total_assets",
    "total_assets": "total_assets",
    "流动资产": "current_assets",
    "流动资产合计": "current_assets",
    "current assets": "current_assets",
    "current_assets": "current_assets",
    "货币资金": "cash_and_equivalents",
    "cash and equivalents": "cash_and_equivalents",
    "cash_and_equivalents": "cash_and_equivalents",
    "应收账款": "accounts_receivable",
    "accounts receivable": "accounts_receivable",
    "accounts_receivable": "accounts_receivable",
    "存货": "inventory",
    "inventory": "inventory",
    "其他应收款": "other_receivables",
    "other receivables": "other_receivables",
    "other_receivables": "other_receivables",
    "固定资产": "fixed_assets",
    "固定资产净额": "fixed_assets",
    "property plant equipment": "fixed_assets",
    "fixed_assets": "fixed_assets",
    "无形资产": "intangible_assets",
    "intangible assets": "intangible_assets",
    "intangible_assets": "intangible_assets",
    "总负债": "total_liabilities",
    "负债合计": "total_liabilities",
    "total liabilities": "total_liabilities",
    "total_liabilities": "total_liabilities",
    "流动负债": "current_liabilities",
    "流动负债合计": "current_liabilities",
    "current liabilities": "current_liabilities",
    "current_liabilities": "current_liabilities",
    "长期负债": "long_term_debt",
    "长期借款": "long_term_debt",
    "long term debt": "long_term_debt",
    "long_term_debt": "long_term_debt",
    "股东权益": "total_equity",
    "股东权益合计": "total_equity",
    "所有者权益": "total_equity",
    "total equity": "total_equity",
    "total_equity": "total_equity",
    # 其他
    "资产减值损失": "asset_impairment_loss",
    "asset impairment loss": "asset_impairment_loss",
    "asset_impairment_loss": "asset_impairment_loss",
    "资本支出": "capital_expenditure",
    "capital expenditure": "capital_expenditure",
    "capital_expenditure": "capital_expenditure",
    "自由现金流": "free_cash_flow",
    "free cash flow": "free_cash_flow",
    "free_cash_flow": "free_cash_flow",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """将中英文列名统一映射为英文字段名"""
    df = df.copy()
    rename_map = {}
    for col in df.columns:
        col_clean = col.strip().lower()
        if col_clean in COLUMN_MAP:
            rename_map[col] = COLUMN_MAP[col_clean]
        # 也尝试直接在映射表中匹配原列名
        elif col.strip() in COLUMN_MAP:
            rename_map[col] = COLUMN_MAP[col.strip()]
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def load_financial_data_from_csv(filepath: str) -> FinancialStatement:
    """从 CSV 文件加载财务数据"""
    df = pd.read_csv(filepath)
    return _df_to_financial_statement(df)


def load_financial_data_from_excel(filepath: str) -> FinancialStatement:
    """从 Excel 文件加载财务数据"""
    df = pd.read_excel(filepath)
    return _df_to_financial_statement(df)


def _df_to_financial_statement(df: pd.DataFrame) -> FinancialStatement:
    """将 DataFrame 转换为 FinancialStatement"""
    df = normalize_columns(df)

    # 尝试识别年份列
    year_col = None
    for col in ["fiscal_year", "year", "会计年度", "年份", "年度"]:
        if col in df.columns:
            year_col = col
            break

    company_name = "未知公司"
    if "公司名称" in df.columns:
        company_name = df["公司名称"].iloc[0]
    elif "company_name" in df.columns:
        company_name = df["company_name"].iloc[0]

    industry = "未知"
    if "行业" in df.columns:
        industry = df["行业"].iloc[0]
    elif "industry" in df.columns:
        industry = df["industry"].iloc[0]

    if year_col:
        fiscal_years = df[year_col].tolist()
        # 逐行构造 FinancialData
        statements = []
        for _, row in df.iterrows():
            fd = _row_to_financial_data(row)
            statements.append(fd)
    else:
        # 如果没有年份列，假设每列是一个年份
        fiscal_years = []
        statements = []
        # 这种情况需要特殊处理：列名是年份，行是科目
        _handle_transposed(df, company_name, industry)

    # 自动补全可计算字段
    _auto_fill(statements)

    return FinancialStatement(
        company_name=company_name,
        industry=industry,
        fiscal_years=fiscal_years,
        statements=statements,
    )


def _row_to_financial_data(row: pd.Series) -> FinancialData:
    """将一行数据转换为 FinancialData"""
    kwargs = {}
    field_names = set(FinancialData.model_fields.keys())
    for field in field_names:
        if field in row.index and pd.notna(row[field]):
            kwargs[field] = float(row[field])
    return FinancialData(**kwargs)


def _auto_fill(statements: list[FinancialData]):
    """自动补全可计算的字段"""
    for stmt in statements:
        if stmt.gross_profit is None and stmt.revenue and stmt.cost_of_revenue:
            stmt.gross_profit = stmt.revenue - stmt.cost_of_revenue
        if stmt.ebit is None and stmt.net_income is not None and (stmt.interest_expense or stmt.income_tax):
            stmt.ebit = stmt.net_income + stmt.interest_expense + stmt.income_tax
        if stmt.free_cash_flow is None and stmt.operating_cash_flow is not None:
            stmt.free_cash_flow = stmt.operating_cash_flow - stmt.capital_expenditure


def _handle_transposed(df: pd.DataFrame, company_name: str, industry: str) -> FinancialStatement:
    """处理转置格式的数据（行=科目，列=年份）"""
    # 暂不实现，对于复杂格式建议使用JSON手动录入
    return FinancialStatement(
        company_name=company_name,
        industry=industry,
        fiscal_years=[],
        statements=[],
    )


def create_financial_statement(
    company_name: str,
    fiscal_years: list[int],
    statements: list[dict],
    industry: str = "未知",
) -> FinancialStatement:
    """从字典列表创建 FinancialStatement（用于手动录入）"""
    fd_list = []
    for s in statements:
        fd_list.append(FinancialData(**s))
    _auto_fill(fd_list)
    return FinancialStatement(
        company_name=company_name,
        industry=industry,
        fiscal_years=fiscal_years,
        statements=fd_list,
    )


def load_financial_data(filepath: str) -> Optional[FinancialStatement]:
    """自动识别文件类型并加载"""
    if filepath.endswith(".csv"):
        return load_financial_data_from_csv(filepath)
    elif filepath.endswith((".xlsx", ".xls")):
        return load_financial_data_from_excel(filepath)
    else:
        raise ValueError(f"不支持的文件格式: {filepath}")
