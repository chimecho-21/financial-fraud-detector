"""
综合报告生成器
整合 M-Score、Z-Score、多维比率分析和 ML 预测结果，
生成结构化的风险评估报告。
"""

from ..models.schemas import (
    FinancialData, FinancialStatement, AnalysisResult,
    MScoreResult, ZScoreResult, RatioAnalysisResult, MLResult,
)
from .m_score import calculate_m_score
from .z_score import calculate_z_score
from .ratios import calculate_financial_ratios
from .ml_predictor import MLPredictor
from .fraud_indicators import calculate_fraud_indicators


# 全局 ML 预测器实例
_predictor = MLPredictor()


def _m_score_to_risk(m_score: float) -> float:
    """将 M-Score 映射为 0-100 风险分"""
    if m_score < -2.22:
        return max(0, (m_score + 4.84) / (2.62) * 30)
    elif m_score < -1.78:
        return 30 + (m_score + 2.22) / 0.44 * 35
    else:
        return 65 + min((m_score + 1.78) / 10, 1) * 35


def _z_score_to_risk(z_score: float) -> float:
    """将 Z-Score 映射为风险分（Z 越低风险越高）"""
    if z_score >= 2.99:
        return max(0, (1 - z_score / 10) * 25)
    elif z_score >= 1.81:
        return 25 + (2.99 - z_score) / 1.18 * 35
    else:
        return 60 + min((1.81 - z_score) / 1.81, 1) * 40


def _get_risk_level(score: float) -> tuple[str, str]:
    """根据综合评分返回风险等级和颜色"""
    if score < 20:
        return "安全", "#22c55e"
    elif score < 40:
        return "低风险", "#eab308"
    elif score < 60:
        return "中风险", "#f97316"
    elif score < 80:
        return "高风险", "#ef4444"
    else:
        return "极高风险", "#7f1d1d"


def _generate_summary(result: AnalysisResult) -> str:
    """生成文字摘要"""
    parts = []

    if result.m_score and result.m_score.is_manipulator:
        parts.append(f"M-Score ({result.m_score.m_score:.2f}) 提示存在盈余操纵可能。")

    if result.z_score and result.z_score.zone == "危险区":
        parts.append(f"Z-Score ({result.z_score.z_score:.2f}) 显示财务风险较高。")

    if result.ratio_analysis:
        ra = result.ratio_analysis.overall_score
        if ra > 50:
            parts.append(f"多维度财务比率分析评分为 {ra:.1f}，存在多项异常指标。")
        elif ra > 30:
            parts.append(f"多维度财务比率分析评分为 {ra:.1f}，部分指标需关注。")
        else:
            parts.append(f"多维度财务比率分析评分 {ra:.1f}，财务指标整体正常。")

    if result.ml_result and result.ml_result.model_available:
        p = result.ml_result.fraud_probability
        if p > 0.5:
            parts.append(f"ML 模型预测造假概率为 {p:.0%}，值得警惕。")

    if not parts:
        parts.append("各项检测结果均未发现明显异常。")

    return " ".join(parts)


def _generate_recommendations(result: AnalysisResult) -> list[str]:
    """根据分析结果生成建议"""
    recs = []

    if result.m_score and result.m_score.is_manipulator:
        recs.append("关注 M-Score 指标异常，重点核查应收账款确认政策和收入确认时点。")

    if result.z_score and result.z_score.zone == "危险区":
        recs.append("企业财务风险较高，建议评估持续经营能力和偿债能力。")

    if result.ratio_analysis:
        for dim in result.ratio_analysis.dimensions:
            if dim.score >= 60:
                if dim.dimension == "收入质量":
                    recs.append("收入质量评分较低，建议核查主要客户的回款情况和收入确认依据。")
                elif dim.dimension == "盈利质量":
                    recs.append("盈利质量不佳，建议分析利润与现金流的差异原因。")
                elif dim.dimension == "资产负债":
                    recs.append("资产负债结构需优化，关注偿债压力和资金链安全。")
                elif dim.dimension == "现金流质量":
                    recs.append("现金流状况需重点关注，核查经营活动现金流的构成。")
                elif dim.dimension == "资产质量":
                    recs.append("资产质量存在隐患，关注减值准备计提是否充分。")

    if result.composite_score >= 40:
        recs.append("综合评分偏高，建议聘请专业审计团队进行深入尽职调查。")

    if not recs:
        recs.append("财务数据表现正常，建议继续保持规范的财务管理和信息披露。")

    return recs


def _normalize_statements(statements: list[FinancialData]):
    """补全可推导的字段"""
    for stmt in statements:
        gp = stmt.gross_profit
        if gp is None and stmt.revenue:
            stmt.gross_profit = stmt.revenue - stmt.cost_of_revenue
        if stmt.ebit is None and stmt.net_income is not None:
            stmt.ebit = stmt.net_income + stmt.interest_expense + stmt.income_tax
        if stmt.free_cash_flow is None and stmt.operating_cash_flow is not None:
            stmt.free_cash_flow = stmt.operating_cash_flow - stmt.capital_expenditure


def generate_report(statement: FinancialStatement) -> AnalysisResult:
    """生成完整分析报告"""
    statements = statement.statements
    fiscal_years = statement.fiscal_years

    # 补全可推导字段
    _normalize_statements(statements)

    # 各模块计算
    m_score_result = calculate_m_score(statements, fiscal_years)
    z_score_result = calculate_z_score(statements, fiscal_years)
    ratio_result = calculate_financial_ratios(statements, fiscal_years)
    ml_result = _predictor.predict(statements)

    # 综合评分
    m_risk = _m_score_to_risk(m_score_result.m_score) if m_score_result else 40
    z_risk = _z_score_to_risk(z_score_result.z_score) if z_score_result else 40
    ratio_risk = ratio_result.overall_score if ratio_result else 40
    ml_risk = ml_result.fraud_probability * 100 if ml_result.model_available else 40

    composite = (0.35 * m_risk + 0.15 * z_risk + 0.30 * ratio_risk + 0.20 * ml_risk)
    composite = round(composite, 1)

    risk_level, color = _get_risk_level(composite)

    # 构建结果
    result = AnalysisResult(
        company_name=statement.company_name,
        fiscal_years=fiscal_years,
        m_score=m_score_result,
        z_score=z_score_result,
        ratio_analysis=ratio_result,
        ml_result=ml_result,
        composite_score=composite,
        risk_level=risk_level,
        risk_level_color=color,
        summary="",
        recommendations=[],
    )

    result.summary = _generate_summary(result)
    result.recommendations = _generate_recommendations(result)

    return result
