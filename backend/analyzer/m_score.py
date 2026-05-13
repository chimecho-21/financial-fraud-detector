"""
Beneish M-Score 模型
用于检测上市公司是否进行了盈余操纵（财务造假）。

M = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
        + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

M > -2.22 → 可能存在盈余操纵
M < -2.22 → 正常
"""

from ..models.schemas import FinancialData, MScoreResult


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    """安全除法，避免除零"""
    if abs(b) < 1e-10:
        return default
    return a / b


def _calc_dsri(curr: FinancialData, prev: FinancialData) -> float:
    """DSRI: 应收账款周转天数指数
    (Receivables_t / Sales_t) / (Receivables_{t-1} / Sales_{t-1})
    应收增长远超营收增长 → 操纵信号
    """
    dsri_t = _safe_div(curr.accounts_receivable, curr.revenue)
    dsri_t1 = _safe_div(prev.accounts_receivable, prev.revenue)
    return _safe_div(dsri_t, dsri_t1, 1.0)


def _calc_gmi(curr: FinancialData, prev: FinancialData) -> float:
    """GMI: 毛利率指数
    GrossMargin_{t-1} / GrossMargin_t
    毛利率恶化 → GMI > 1 → 操纵动机增强
    """
    gp_t = curr.gross_profit if curr.gross_profit is not None else curr.revenue - curr.cost_of_revenue
    gp_t1 = prev.gross_profit if prev.gross_profit is not None else prev.revenue - prev.cost_of_revenue
    gm_t = _safe_div(gp_t, curr.revenue)
    gm_t1 = _safe_div(gp_t1, prev.revenue)
    return _safe_div(gm_t1, gm_t, 1.0)


def _calc_aqi(curr: FinancialData, prev: FinancialData) -> float:
    """AQI: 资产质量指数
    [1 - (CurrentAssets_t + PPE_t) / TotalAssets_t] /
    [1 - (CurrentAssets_{t-1} + PPE_{t-1}) / TotalAssets_{t-1}]
    资产质量下降 → AQI > 1 → 操纵信号
    """
    non_current_ratio_t = 1.0 - _safe_div(curr.current_assets + curr.fixed_assets, curr.total_assets)
    non_current_ratio_t1 = 1.0 - _safe_div(prev.current_assets + prev.fixed_assets, prev.total_assets)
    return _safe_div(non_current_ratio_t, non_current_ratio_t1, 1.0)


def _calc_sgi(curr: FinancialData, prev: FinancialData) -> float:
    """SGI: 营收增长指数
    Sales_t / Sales_{t-1}
    高速增长 → 可能伴随操纵
    """
    return _safe_div(curr.revenue, prev.revenue, 1.0)


def _calc_depi(curr: FinancialData, prev: FinancialData) -> float:
    """DEPI: 折旧指数
    (Depreciation_{t-1} / PPE_{t-1}) / (Depreciation_t / PPE_t)
    折旧率下降 → 可能虚增利润
    """
    dep_rate_t = _safe_div(curr.depreciation, curr.fixed_assets)
    dep_rate_t1 = _safe_div(prev.depreciation, prev.fixed_assets)
    return _safe_div(dep_rate_t1, dep_rate_t, 1.0)


def _calc_sgai(curr: FinancialData, prev: FinancialData) -> float:
    """SGAI: 销售管理费用指数
    (SG&A_t / Sales_t) / (SG&A_{t-1} / Sales_{t-1})
    费用比例上升 → 负面信号
    """
    sga_ratio_t = _safe_div(curr.sg_and_a, curr.revenue)
    sga_ratio_t1 = _safe_div(prev.sg_and_a, prev.revenue)
    return _safe_div(sga_ratio_t, sga_ratio_t1, 1.0)


def _calc_lvgi(curr: FinancialData, prev: FinancialData) -> float:
    """LVGI: 杠杆指数
    (TotalDebt_t / TotalAssets_t) / (TotalDebt_{t-1} / TotalAssets_{t-1})
    杠杆上升 → 融资压力 → 操纵动机
    """
    leverage_t = _safe_div(curr.total_liabilities, curr.total_assets)
    leverage_t1 = _safe_div(prev.total_liabilities, prev.total_assets)
    return _safe_div(leverage_t, leverage_t1, 1.0)


def _calc_tata(curr: FinancialData) -> float:
    """TATA: 应计项目占总资产比
    (NetIncome_t - OperatingCashFlow_t) / TotalAssets_t
    应计利润过高 → 操纵信号
    """
    return _safe_div(curr.net_income - curr.operating_cash_flow, curr.total_assets)


def calculate_m_score(statements: list[FinancialData], fiscal_years: list[int]) -> MScoreResult:
    """计算 Beneish M-Score"""
    result = MScoreResult()

    if len(statements) < 2:
        result.description = "需要至少两年的财务数据才能计算 M-Score"
        return result

    # 使用最近两年数据
    curr = statements[-1]
    prev = statements[-2]

    result.dsri = _calc_dsri(curr, prev)
    result.gmi = _calc_gmi(curr, prev)
    result.aqi = _calc_aqi(curr, prev)
    result.sgi = _calc_sgi(curr, prev)
    result.depi = _calc_depi(curr, prev)
    result.sgai = _calc_sgai(curr, prev)
    result.lvgi = _calc_lvgi(curr, prev)
    result.tata = _calc_tata(curr)

    # 计算综合 M-Score
    result.m_score = (
        -4.84
        + 0.92 * result.dsri
        + 0.528 * result.gmi
        + 0.404 * result.aqi
        + 0.892 * result.sgi
        + 0.115 * result.depi
        - 0.172 * result.sgai
        + 4.679 * result.tata
        - 0.327 * result.lvgi
    )

    result.is_manipulator = result.m_score > -2.22

    if result.m_score < -2.22:
        result.description = f"M-Score = {result.m_score:.3f} < -2.22，未发现明显的盈余操纵迹象。"
    elif result.m_score < -1.78:
        result.description = f"M-Score = {result.m_score:.3f}，处于灰色区域，存在一定盈余操纵可能性。"
    else:
        result.description = f"M-Score = {result.m_score:.3f} > -1.78，存在较高的盈余操纵嫌疑！"

    return result
