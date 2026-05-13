"""
多维度财务比率分析引擎
从 7 个维度评估财务数据异常程度，每个维度包含多个指标。
分值范围 0-100，越高代表风险越大。
"""

from typing import Optional
from ..models.schemas import (
    FinancialData, IndicatorScore, DimensionScore, RatioAnalysisResult,
)


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    if abs(b) < 1e-10:
        return default
    return a / b


def _risk_score(value: float, threshold_low: float, threshold_high: float,
                higher_is_risk: bool = True) -> float:
    """将指标值映射为 0-100 的风险分

    如果 higher_is_risk=True: 值越高风险越大
    使用阈值确定风险范围，超出阈值的部分线性映射到 50-100 区间，
    阈值以内的部分映射到 0-50。
    """
    if higher_is_risk:
        if value <= threshold_low:
            return max(0, value / threshold_low * 30) if threshold_low > 0 else 0
        elif value <= threshold_high:
            ratio = (value - threshold_low) / (threshold_high - threshold_low)
            return 30 + ratio * 40
        else:
            ratio = min((value - threshold_high) / threshold_high, 2.0)
            return 70 + ratio * 15
    else:
        # 越低越危险：对低值给高分
        if value >= threshold_high:
            return max(0, (1 - value / (threshold_high * 3)) * 30) if threshold_high > 0 else 0
        elif value >= threshold_low:
            ratio = (threshold_high - value) / (threshold_high - threshold_low)
            return 30 + ratio * 40
        else:
            ratio = min((threshold_low - value) / threshold_low, 2.0)
            return 70 + ratio * 15


def _signal(score: float) -> tuple[str, str]:
    """根据分值返回信号和描述"""
    if score < 30:
        return "正常", "normal"
    elif score < 60:
        return "警告", "warning"
    else:
        return "危险", "danger"


def calc_revenue_quality(curr: FinancialData, prev: FinancialData) -> DimensionScore:
    """收入质量维度"""
    indicators = []

    # 1. 营收增长 vs 应收账款增长
    revenue_growth = _safe_div(curr.revenue - prev.revenue, prev.revenue)
    ar_growth = _safe_div(
        curr.accounts_receivable - prev.accounts_receivable,
        prev.accounts_receivable,
    )
    ar_revenue_gap = ar_growth - revenue_growth
    # 应收增速超过营收增速 20% 以上视为风险
    score_ar = _risk_score(ar_revenue_gap, 0.1, 0.3, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="应收账款增长与营收增长差异",
        score=round(score_ar, 1),
        value=round(ar_revenue_gap, 4),
        threshold=f"营收增速: {revenue_growth:.1%}, 应收增速: {ar_growth:.1%}",
        signal=_signal(score_ar)[0],
        detail="应收增速远超营收增速 → 收入可能虚增",
    ))

    # 2. 应收账款 / 营业收入
    ar_to_revenue = _safe_div(curr.accounts_receivable, curr.revenue)
    score_ar_ratio = _risk_score(ar_to_revenue, 0.15, 0.3, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="应收账款 / 营业收入",
        score=round(score_ar_ratio, 1),
        value=round(ar_to_revenue, 4),
        threshold=f"安全<15%, 警告15-30%, 危险>30%",
        signal=_signal(score_ar_ratio)[0],
        detail="应收账款占比过高 → 收入确认可能不审慎",
    ))

    overall = (score_ar + score_ar_ratio) / 2
    return DimensionScore(
        dimension="收入质量",
        score=round(overall, 1),
        weight=0.20,
        indicators=indicators,
    )


def calc_earnings_quality(curr: FinancialData, prev: FinancialData) -> DimensionScore:
    """盈利质量维度"""
    indicators = []

    # 1. 经营现金流 / 净利润
    ocf_to_ni = _safe_div(curr.operating_cash_flow, curr.net_income)
    # 正常应接近 1，远小于 1 说明利润无现金支撑
    score_ocf = _risk_score(abs(1 - ocf_to_ni), 0.2, 0.5, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="经营现金流 / 净利润",
        score=round(score_ocf, 1),
        value=round(ocf_to_ni, 4),
        threshold=f"正常 0.8-1.2, 当前: {ocf_to_ni:.2f}",
        signal=_signal(score_ocf)[0],
        detail="比值持续 < 1 → 利润缺乏现金支撑",
    ))

    # 2. 毛利率变化
    gp_t = curr.gross_profit if curr.gross_profit is not None else curr.revenue - curr.cost_of_revenue
    gp_t1 = prev.gross_profit if prev.gross_profit is not None else prev.revenue - prev.cost_of_revenue
    gm_t = _safe_div(gp_t, curr.revenue)
    gm_t1 = _safe_div(gp_t1, prev.revenue)
    gm_change = gm_t - gm_t1
    score_gm = _risk_score(abs(gm_change), 0.05, 0.15, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="毛利率变动",
        score=round(score_gm, 1),
        value=round(gm_change, 4),
        threshold=f"上期: {gm_t1:.1%}, 本期: {gm_t:.1%}",
        signal=_signal(score_gm)[0],
        detail="毛利率剧烈波动 → 可能虚增收入或隐瞒成本",
    ))

    overall = (score_ocf + score_gm) / 2
    return DimensionScore(
        dimension="盈利质量",
        score=round(overall, 1),
        weight=0.20,
        indicators=indicators,
    )


def calc_balance_sheet_risk(curr: FinancialData, prev: FinancialData) -> DimensionScore:
    """资产负债风险维度"""
    indicators = []

    # 1. 资产负债率
    debt_ratio = _safe_div(curr.total_liabilities, curr.total_assets)
    score_debt = _risk_score(debt_ratio, 0.5, 0.7, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="资产负债率",
        score=round(score_debt, 1),
        value=round(debt_ratio, 4),
        threshold=f"安全<50%, 警告50-70%, 危险>70%",
        signal=_signal(score_debt)[0],
        detail="负债率过高 → 财务压力大，操纵动机增强",
    ))

    # 2. 其他应收款占比
    other_re_ratio = _safe_div(curr.other_receivables, curr.total_assets)
    score_other = _risk_score(other_re_ratio, 0.03, 0.08, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="其他应收款 / 总资产",
        score=round(score_other, 1),
        value=round(other_re_ratio, 4),
        threshold=f"安全<3%, 警告3-8%, 危险>8%",
        signal=_signal(score_other)[0],
        detail="其他应收款异常升高 → 资金可能被占用或体外循环",
    ))

    # 3. 存货 / 营业收入
    inv_to_rev = _safe_div(curr.inventory, curr.revenue)
    score_inv = _risk_score(inv_to_rev, 0.15, 0.30, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="存货 / 营业收入",
        score=round(score_inv, 1),
        value=round(inv_to_rev, 4),
        threshold=f"安全<15%, 警告15-30%, 危险>30%",
        signal=_signal(score_inv)[0],
        detail="存货异常堆积 → 可能虚增存货或隐瞒滞销",
    ))

    # 4. 应收账款 / 总资产
    ar_to_assets = _safe_div(curr.accounts_receivable, curr.total_assets)
    score_ar_assets = _risk_score(ar_to_assets, 0.1, 0.2, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="应收账款 / 总资产",
        score=round(score_ar_assets, 1),
        value=round(ar_to_assets, 4),
        threshold=f"安全<10%, 警告10-20%, 危险>20%",
        signal=_signal(score_ar_assets)[0],
        detail="应收占比过高 → 资产质量下降",
    ))

    overall = (score_debt + score_other + score_inv + score_ar_assets) / 4
    return DimensionScore(
        dimension="资产负债",
        score=round(overall, 1),
        weight=0.20,
        indicators=indicators,
    )


def calc_operating_efficiency(curr: FinancialData, prev: FinancialData) -> DimensionScore:
    """运营效率维度"""
    indicators = []

    # 1. 总资产周转率变化
    asset_turn_t = _safe_div(curr.revenue, curr.total_assets)
    asset_turn_t1 = _safe_div(prev.revenue, prev.total_assets)
    turn_change = _safe_div(asset_turn_t - asset_turn_t1, asset_turn_t1)
    score_turn = _risk_score(abs(turn_change), 0.1, 0.25, higher_is_risk=True)
    indicators.append(IndicatorScore(
        name="总资产周转率变动",
        score=round(score_turn, 1),
        value=round(turn_change, 4),
        threshold=f"上期: {asset_turn_t1:.2f}, 本期: {asset_turn_t:.2f}",
        signal=_signal(score_turn)[0],
        detail="周转率异常变化 → 收入或资产可能失真",
    ))

    overall = score_turn
    return DimensionScore(
        dimension="运营效率",
        score=round(overall, 1),
        weight=0.10,
        indicators=indicators,
    )


def calc_cash_flow_risk(curr: FinancialData, prev: FinancialData) -> DimensionScore:
    """现金流风险维度"""
    indicators = []

    # 1. 经营现金流 / 营业收入
    ocf_to_rev = _safe_div(curr.operating_cash_flow, curr.revenue)
    score_ocf_rev = _risk_score(ocf_to_rev, 0.05, 0.0, higher_is_risk=False)
    indicators.append(IndicatorScore(
        name="经营现金流 / 营业收入",
        score=round(score_ocf_rev, 1),
        value=round(ocf_to_rev, 4),
        threshold=f"经营现金流占营收比例: {ocf_to_rev:.1%}",
        signal=_signal(score_ocf_rev)[0],
        detail="经营现金流占比过低 → 收入质量差",
    ))

    # 2. 自由现金流趋势
    fcf_t = (curr.free_cash_flow if curr.free_cash_flow is not None
             else curr.operating_cash_flow - curr.capital_expenditure)
    fcf_t1 = (prev.free_cash_flow if prev.free_cash_flow is not None
              else prev.operating_cash_flow - prev.capital_expenditure)

    if abs(fcf_t1) > 1e-10:
        fcf_change = _safe_div(fcf_t - fcf_t1, abs(fcf_t1))
        score_fcf = _risk_score(abs(fcf_change), 0.3, 0.8, higher_is_risk=True)
        signal_text = _signal(score_fcf)[0]
        detail = "自由现金流剧烈波动 → 财务稳定性差"
    else:
        score_fcf = 0 if fcf_t >= 0 else 50
        signal_text = "正常" if fcf_t >= 0 else "警告"
        detail = "自由现金流状况"
    indicators.append(IndicatorScore(
        name="自由现金流变化",
        score=round(score_fcf, 1),
        value=round(fcf_t, 2),
        threshold=f"本期: {fcf_t:.0f}, 上期: {fcf_t1:.0f}",
        signal=signal_text,
        detail=detail,
    ))

    overall = (score_ocf_rev + score_fcf) / 2
    return DimensionScore(
        dimension="现金流质量",
        score=round(overall, 1),
        weight=0.15,
        indicators=indicators,
    )


def calc_asset_quality(curr: FinancialData, prev: FinancialData) -> DimensionScore:
    """资产质量维度"""
    indicators = []

    # 1. 资产减值损失变动
    if abs(prev.asset_impairment_loss) > 1e-10:
        impairment_change = _safe_div(
            curr.asset_impairment_loss - prev.asset_impairment_loss,
            abs(prev.asset_impairment_loss),
        )
        score_impair = _risk_score(abs(impairment_change), 0.3, 0.5, higher_is_risk=True)
        indicators.append(IndicatorScore(
            name="资产减值损失变动",
            score=round(score_impair, 1),
            value=round(impairment_change, 4),
            threshold=f"变化幅度: {abs(impairment_change):.0%}",
            signal=_signal(score_impair)[0],
            detail="资产减值损失突然大幅变动 → 可能有一次性利润调节",
        ))
        overall = score_impair
    else:
        overall = 0
        indicators.append(IndicatorScore(
            name="资产减值损失变动",
            score=0,
            value=0,
            threshold="历史数据不足",
            signal="正常",
            detail="无前期数据对比",
        ))

    return DimensionScore(
        dimension="资产质量",
        score=round(overall, 1),
        weight=0.10,
        indicators=indicators,
    )


def calc_growth_risk(curr: FinancialData, prev: FinancialData) -> DimensionScore:
    """成长风险维度"""
    indicators = []

    # 营收过度增长风险
    revenue_growth = _safe_div(curr.revenue - prev.revenue, prev.revenue)
    if revenue_growth > 0.5:
        score_growth = min((revenue_growth - 0.5) * 100, 90)
        signal_text = _signal(score_growth)[0]
        indicators.append(IndicatorScore(
            name="营收增长率",
            score=round(score_growth, 1),
            value=round(revenue_growth, 4),
            threshold=f"增长率: {revenue_growth:.1%}",
            signal=signal_text,
            detail="营收增长超过50% → 高速增长企业操纵风险较高",
        ))
    else:
        indicators.append(IndicatorScore(
            name="营收增长率",
            score=0,
            value=round(revenue_growth, 4),
            threshold=f"增长率: {revenue_growth:.1%}",
            signal="正常",
            detail="营收增长在合理范围内",
        ))
        score_growth = 0

    return DimensionScore(
        dimension="成长风险",
        score=round(score_growth, 1),
        weight=0.05,
        indicators=indicators,
    )


def calculate_financial_ratios(statements: list[FinancialData],
                                fiscal_years: list[int]) -> RatioAnalysisResult:
    """计算多维度财务比率分析"""
    if len(statements) < 2:
        return RatioAnalysisResult(
            dimensions=[],
            overall_score=0,
        )

    curr = statements[-1]
    prev = statements[-2]

    dimensions = [
        calc_revenue_quality(curr, prev),
        calc_earnings_quality(curr, prev),
        calc_balance_sheet_risk(curr, prev),
        calc_operating_efficiency(curr, prev),
        calc_cash_flow_risk(curr, prev),
        calc_asset_quality(curr, prev),
        calc_growth_risk(curr, prev),
    ]

    # 加权综合得分
    overall = sum(d.score * d.weight for d in dimensions)

    return RatioAnalysisResult(
        dimensions=dimensions,
        overall_score=round(overall, 1),
    )


def score_ratios(ratio_result: RatioAnalysisResult) -> float:
    """返回比率分析的综合风险分（0-100）"""
    return ratio_result.overall_score
