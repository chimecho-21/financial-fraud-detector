"""
生成示例财务数据用于测试
包含正常公司和财务造假特征的公司数据对比
"""

from ..models.schemas import FinancialData, FinancialStatement


def generate_normal_company() -> FinancialStatement:
    """生成财务状况正常的公司示例数据（3年）"""
    return FinancialStatement(
        company_name="稳健科技股份有限公司",
        industry="信息技术",
        fiscal_years=[2021, 2022, 2023],
        statements=[
            FinancialData(
                revenue=100000,
                cost_of_revenue=60000,
                sg_and_a=15000,
                depreciation=5000,
                net_income=15000,
                interest_expense=1000,
                income_tax=4000,
                operating_cash_flow=18000,
                total_assets=200000,
                current_assets=120000,
                cash_and_equivalents=30000,
                accounts_receivable=15000,
                inventory=10000,
                other_receivables=2000,
                fixed_assets=60000,
                intangible_assets=5000,
                total_liabilities=80000,
                current_liabilities=50000,
                long_term_debt=20000,
                total_equity=120000,
                asset_impairment_loss=1000,
                capital_expenditure=8000,
            ),
            FinancialData(
                revenue=120000,
                cost_of_revenue=72000,
                sg_and_a=17000,
                depreciation=5500,
                net_income=18000,
                interest_expense=1200,
                income_tax=5000,
                operating_cash_flow=20000,
                total_assets=220000,
                current_assets=130000,
                cash_and_equivalents=35000,
                accounts_receivable=16000,
                inventory=12000,
                other_receivables=2500,
                fixed_assets=65000,
                intangible_assets=6000,
                total_liabilities=85000,
                current_liabilities=55000,
                long_term_debt=22000,
                total_equity=135000,
                asset_impairment_loss=1200,
                capital_expenditure=9000,
            ),
            FinancialData(
                revenue=140000,
                cost_of_revenue=84000,
                sg_and_a=19000,
                depreciation=6000,
                net_income=22000,
                interest_expense=1500,
                income_tax=6000,
                operating_cash_flow=24000,
                total_assets=250000,
                current_assets=150000,
                cash_and_equivalents=45000,
                accounts_receivable=18000,
                inventory=14000,
                other_receivables=3000,
                fixed_assets=70000,
                intangible_assets=8000,
                total_liabilities=95000,
                current_liabilities=60000,
                long_term_debt=25000,
                total_equity=155000,
                asset_impairment_loss=1100,
                capital_expenditure=10000,
            ),
        ],
    )


def generate_fraud_company() -> FinancialStatement:
    """生成存在财务造假特征的公司示例数据（3年）"""
    return FinancialStatement(
        company_name="风险贸易集团有限公司",
        industry="批发零售",
        fiscal_years=[2021, 2022, 2023],
        statements=[
            FinancialData(
                revenue=80000,
                cost_of_revenue=55000,
                sg_and_a=12000,
                depreciation=4000,
                net_income=8000,
                interest_expense=3000,
                income_tax=2000,
                operating_cash_flow=5000,
                total_assets=150000,
                current_assets=100000,
                cash_and_equivalents=10000,
                accounts_receivable=25000,
                inventory=20000,
                other_receivables=12000,
                fixed_assets=35000,
                intangible_assets=5000,
                total_liabilities=105000,
                current_liabilities=70000,
                long_term_debt=30000,
                total_equity=45000,
                asset_impairment_loss=500,
                capital_expenditure=6000,
            ),
            FinancialData(
                revenue=110000,
                cost_of_revenue=75000,
                sg_and_a=16000,
                depreciation=4200,
                net_income=10000,
                interest_expense=4000,
                income_tax=2500,
                operating_cash_flow=4000,
                total_assets=200000,
                current_assets=140000,
                cash_and_equivalents=8000,
                accounts_receivable=40000,
                inventory=30000,
                other_receivables=20000,
                fixed_assets=38000,
                intangible_assets=8000,
                total_liabilities=145000,
                current_liabilities=95000,
                long_term_debt=40000,
                total_equity=55000,
                asset_impairment_loss=3000,
                capital_expenditure=8000,
            ),
            FinancialData(
                revenue=160000,
                cost_of_revenue=108000,
                sg_and_a=24000,
                depreciation=4500,
                net_income=15000,
                interest_expense=5500,
                income_tax=4000,
                operating_cash_flow=3000,
                total_assets=260000,
                current_assets=180000,
                cash_and_equivalents=5000,
                accounts_receivable=65000,
                inventory=45000,
                other_receivables=30000,
                fixed_assets=40000,
                intangible_assets=12000,
                total_liabilities=195000,
                current_liabilities=125000,
                long_term_debt=55000,
                total_equity=65000,
                asset_impairment_loss=8000,
                capital_expenditure=10000,
            ),
        ],
    )


def generate_company_list() -> list[FinancialStatement]:
    """生成示例公司列表"""
    return [
        generate_normal_company(),
        generate_fraud_company(),
    ]


def get_sample_statement(name: str = "normal") -> FinancialStatement:
    """按名称获取示例数据"""
    if name == "fraud":
        return generate_fraud_company()
    return generate_normal_company()
