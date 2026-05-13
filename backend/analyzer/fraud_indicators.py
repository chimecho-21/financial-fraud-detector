"""
财务造假指标综合计算
整合 M-Score、Z-Score 和多维财务比率分析
"""

from ..models.schemas import FinancialData, FinancialStatement, IndicatorScore


def calculate_fraud_indicators(statement: FinancialStatement) -> dict:
    """计算所有造假检测指标，返回结构化结果"""
    statements = statement.statements
    fiscal_years = statement.fiscal_years
    curr = statements[-1] if statements else None
    prev = statements[-2] if len(statements) >= 2 else None

    indicators = []

    if not curr:
        return {"indicators": [], "overview": "缺少财务数据"}

    # 1. 现金含量
    if curr.net_income and curr.operating_cash_flow:
        cash_ratio = curr.operating_cash_flow / curr.net_income if curr.net_income != 0 else 0
        cash_indicator = IndicatorScore(
            name="现金含量（经营现金流/净利润）",
            score=round(abs(1 - cash_ratio) * 100, 1),
            value=round(cash_ratio, 4),
            threshold=f"正常 ≈ 1.0",
            signal="警告" if abs(1 - cash_ratio) > 0.5 else ("关注" if abs(1 - cash_ratio) > 0.2 else "正常"),
            detail="反映利润的现金保障程度",
        )
        indicators.append(cash_indicator)

    # 2. 应收占比
    if curr.revenue and curr.accounts_receivable:
        ar_ratio = curr.accounts_receivable / curr.revenue
        indicators.append(IndicatorScore(
            name="应收账款占营收比",
            score=round(min(ar_ratio / 0.3 * 100, 100), 1),
            value=round(ar_ratio, 4),
            threshold="安全 < 15%",
            signal="危险" if ar_ratio > 0.3 else ("警告" if ar_ratio > 0.15 else "正常"),
            detail="应收账款占比过高意味着收入可能缺乏真实现金流支撑",
        ))

    # 3. 资产负债率
    if curr.total_assets and curr.total_liabilities:
        debt_ratio = curr.total_liabilities / curr.total_assets
        indicators.append(IndicatorScore(
            name="资产负债率",
            score=round(min(debt_ratio / 0.7 * 100, 100), 1),
            value=round(debt_ratio, 4),
            threshold="安全 < 50%",
            signal="危险" if debt_ratio > 0.7 else ("警告" if debt_ratio > 0.5 else "正常"),
            detail="高负债率意味着偿债压力大，操纵财务的动机增强",
        ))

    # 4. 营收增长 vs 资产增长
    if prev and curr.revenue and prev.revenue and curr.total_assets and prev.total_assets:
        rev_growth = (curr.revenue - prev.revenue) / prev.revenue
        asset_growth = (curr.total_assets - prev.total_assets) / prev.total_assets
        gap = rev_growth - asset_growth
        indicators.append(IndicatorScore(
            name="营收增长 vs 资产增长",
            score=round(min(abs(gap) * 100, 100), 1),
            value=round(gap, 4),
            threshold=f"营收增: {rev_growth:.1%}, 资产增: {asset_growth:.1%}",
            signal="危险" if abs(gap) > 0.3 else ("警告" if abs(gap) > 0.15 else "正常"),
            detail="营收增长远超资产增长 → 可能存在收入虚增",
        ))

    # 5. 其他应收款占比
    if curr.total_assets and curr.other_receivables:
        other_re_ratio = curr.other_receivables / curr.total_assets
        indicators.append(IndicatorScore(
            name="其他应收款占总资产比",
            score=round(min(other_re_ratio / 0.08 * 100, 100), 1),
            value=round(other_re_ratio, 4),
            threshold="安全 < 3%",
            signal="危险" if other_re_ratio > 0.08 else ("警告" if other_re_ratio > 0.03 else "正常"),
            detail="其他应收款异常高 → 资金可能被关联方占用",
        ))

    # 6. 存货占比
    if curr.revenue and curr.inventory:
        inv_ratio = curr.inventory / curr.revenue
        indicators.append(IndicatorScore(
            name="存货占营收比",
            score=round(min(inv_ratio / 0.3 * 100, 100), 1),
            value=round(inv_ratio, 4),
            threshold="安全 < 15%",
            signal="危险" if inv_ratio > 0.3 else ("警告" if inv_ratio > 0.15 else "正常"),
            detail="存货异常堆积 → 可能隐瞒滞销或虚增存货",
        ))

    # 7. 毛利率变动
    if prev:
        gp_t = curr.gross_profit if curr.gross_profit is not None else curr.revenue - curr.cost_of_revenue
        gp_t1 = prev.gross_profit if prev.gross_profit is not None else prev.revenue - prev.cost_of_revenue
        gm_t = gp_t / curr.revenue if curr.revenue else 0
        gm_t1 = gp_t1 / prev.revenue if prev.revenue else 0
        gm_change = abs(gm_t - gm_t1)
        indicators.append(IndicatorScore(
            name="毛利率变动幅度",
            score=round(min(gm_change / 0.15 * 100, 100), 1),
            value=round(gm_t - gm_t1, 4),
            threshold=f"上期: {gm_t1:.1%}, 本期: {gm_t:.1%}",
            signal="危险" if gm_change > 0.15 else ("警告" if gm_change > 0.05 else "正常"),
            detail="毛利率剧烈波动 → 可能通过调整收入/成本操纵利润",
        ))

    # 计算平均风险分
    avg_score = sum(ind.score for ind in indicators) / len(indicators) if indicators else 0

    return {
        "indicators": [ind.model_dump() for ind in indicators],
        "count": len(indicators),
        "avg_score": round(avg_score, 1),
        "overview": _get_overview(avg_score),
    }


def _get_overview(avg_score: float) -> str:
    if avg_score < 20:
        return "各项指标均在正常范围内"
    elif avg_score < 40:
        return "少数指标出现异常，建议关注"
    elif avg_score < 60:
        return "多项指标异常，存在一定财务风险"
    elif avg_score < 80:
        return "大量指标异常，财务风险较高，建议深入调查"
    else:
        return "几乎全部指标均指向异常，极高概率存在财务造假"
