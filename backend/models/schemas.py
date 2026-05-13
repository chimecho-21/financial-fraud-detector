from typing import Optional
from pydantic import BaseModel, Field


class FinancialData(BaseModel):
    """单期财务数据"""
    model_config = {"populate_by_name": True}

    # 损益表
    revenue: float = Field(0, description="营业收入")
    cost_of_revenue: float = Field(0, description="营业成本")
    gross_profit: Optional[float] = Field(None, description="毛利")
    sg_and_a: float = Field(0, description="销售管理费用")
    depreciation: float = Field(0, description="折旧摊销")
    net_income: float = Field(0, description="净利润")
    interest_expense: float = Field(0, description="利息支出")
    income_tax: float = Field(0, description="所得税")
    ebit: Optional[float] = Field(None, description="息税前利润")
    operating_cash_flow: float = Field(0, description="经营活动现金流净额")
    # 资产负债表
    total_assets: float = Field(0, description="总资产")
    current_assets: float = Field(0, description="流动资产")
    cash_and_equivalents: float = Field(0, description="货币资金")
    accounts_receivable: float = Field(0, description="应收账款净额")
    inventory: float = Field(0, description="存货净额")
    other_receivables: float = Field(0, description="其他应收款")
    fixed_assets: float = Field(0, description="固定资产净额")
    intangible_assets: float = Field(0, description="无形资产")
    total_liabilities: float = Field(0, description="总负债")
    current_liabilities: float = Field(0, description="流动负债")
    long_term_debt: float = Field(0, description="长期负债")
    total_equity: float = Field(0, description="股东权益合计")
    # 其他
    asset_impairment_loss: float = Field(0, description="资产减值损失")
    free_cash_flow: Optional[float] = Field(None, description="自由现金流")
    capital_expenditure: float = Field(0, description="资本支出")


class FinancialStatement(BaseModel):
    """包含公司信息和多年财务数据"""
    company_name: str = Field(..., description="公司名称")
    industry: str = Field("未知", description="所属行业")
    fiscal_years: list[int] = Field(..., description="会计年度列表")
    statements: list[FinancialData] = Field(..., description="各年度财务数据")


class MScoreResult(BaseModel):
    """M-Score 计算结果"""
    dsri: float = 0  # 应收账款周转天数指数
    gmi: float = 0   # 毛利率指数
    aqi: float = 0   # 资产质量指数
    sgi: float = 0   # 营收增长指数
    depi: float = 0  # 折旧指数
    sgai: float = 0  # 销售管理费用指数
    lvgi: float = 0  # 杠杆指数
    tata: float = 0  # 应计项目占总资产比
    m_score: float = 0  # 综合 M-Score
    is_manipulator: bool = False
    description: str = ""


class ZScoreResult(BaseModel):
    """Z-Score 计算结果"""
    z_score: float = 0
    z1: Optional[float] = None  # 制造企业
    z2: Optional[float] = None  # 非制造企业
    z3: Optional[float] = None  # 新兴市场企业
    zone: str = ""  # 安全区/灰色区/危险区
    description: str = ""


class IndicatorScore(BaseModel):
    """单项指标评分"""
    name: str
    score: float   # 0-100, 越高越危险
    value: float
    threshold: str
    signal: str  # "正常" / "警告" / "危险"
    detail: str


class DimensionScore(BaseModel):
    """维度评分"""
    dimension: str  # 收入质量、盈利质量等
    score: float    # 0-100
    weight: float
    indicators: list[IndicatorScore]


class RatioAnalysisResult(BaseModel):
    """财务比率分析结果"""
    dimensions: list[DimensionScore]
    overall_score: float = 0  # 0-100


class MLResult(BaseModel):
    """机器学习预测结果"""
    fraud_probability: float = 0   # 0-1
    prediction: str = "未启用"
    feature_importance: dict[str, float] = {}
    model_available: bool = False
    description: str = ""


class AnalysisResult(BaseModel):
    """综合分析结果"""
    company_name: str
    fiscal_years: list[int]
    m_score: Optional[MScoreResult] = None
    z_score: Optional[ZScoreResult] = None
    ratio_analysis: Optional[RatioAnalysisResult] = None
    ml_result: Optional[MLResult] = None
    composite_score: float = 0     # 0-100
    risk_level: str = ""           # 安全/低风险/中风险/高风险/极高风险
    risk_level_color: str = ""
    summary: str = ""
    recommendations: list[str] = []
