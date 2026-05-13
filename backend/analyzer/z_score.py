"""
Altman Z-Score 破产风险模型
用于预测企业破产风险，Z-Score 较低的公司财务造假动机更强。

Z1 (制造企业): 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5
Z2 (非制造企业): 6.56X1 + 3.26X2 + 6.72X3 + 1.05X4
Z3 (新兴市场): 3.25 + 6.56X1 + 3.26X2 + 6.72X3 + 1.05X4
"""

from ..models.schemas import FinancialData, ZScoreResult


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    if abs(b) < 1e-10:
        return default
    return a / b


def _calc_x1(curr: FinancialData) -> float:
    """X1 = 营运资本 / 总资产"""
    working_capital = curr.current_assets - curr.current_liabilities
    return _safe_div(working_capital, curr.total_assets)


def _calc_x2(curr: FinancialData) -> float:
    """X2 = 留存收益 / 总资产
    注：当无法获取留存收益时，使用股东权益近似
    """
    # 多数财务数据不单独提供留存收益，使用股东权益近似
    return _safe_div(curr.total_equity, curr.total_assets)


def _calc_x3(curr: FinancialData) -> float:
    """X3 = EBIT / 总资产"""
    ebit = curr.ebit if curr.ebit is not None else curr.net_income + curr.interest_expense
    return _safe_div(ebit, curr.total_assets)


def _calc_x4(curr: FinancialData) -> float:
    """X4 = 权益市值 / 负债账面价值
    注：当无法获取市值时，使用账面权益替代
    """
    return _safe_div(curr.total_equity, curr.total_liabilities)


def _calc_x5(curr: FinancialData) -> float:
    """X5 = 营业收入 / 总资产"""
    return _safe_div(curr.revenue, curr.total_assets)


def calculate_z_score(statements: list[FinancialData], fiscal_years: list[int]) -> ZScoreResult:
    """计算 Altman Z-Score"""
    result = ZScoreResult()

    if not statements:
        result.description = "没有财务数据"
        return result

    curr = statements[-1]

    x1 = _calc_x1(curr)
    x2 = _calc_x2(curr)
    x3 = _calc_x3(curr)
    x4 = _calc_x4(curr)
    x5 = _calc_x5(curr)

    # Z1: 适用于制造企业
    z1 = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
    result.z1 = round(z1, 4)

    # Z2: 适用于非制造企业
    z2 = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
    result.z2 = round(z2, 4)

    # Z3: 适用于新兴市场企业
    z3 = 3.25 + 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
    result.z3 = round(z3, 4)

    # 默认使用 Z1
    result.z_score = z1

    if z1 >= 2.99:
        result.zone = "安全区"
        result.description = f"Z-Score = {z1:.3f} >= 2.99，企业财务状况良好，破产风险较低。"
    elif z1 >= 1.81:
        result.zone = "灰色区"
        result.description = f"Z-Score = {z1:.3f}，处于灰色区域，存在一定的财务风险。"
    else:
        result.zone = "危险区"
        result.description = f"Z-Score = {z1:.3f} < 1.81，财务风险较高，需警惕破产和造假风险。"

    return result
