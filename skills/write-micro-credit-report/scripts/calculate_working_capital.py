# -*- coding: utf-8 -*-
"""
小微企业一般授信业务 - 营运资金需求量测算与指标计算工具
依据：银监会《流动资金贷款管理暂行办法》营运资金需求量测算标准公式
"""

import sys, json

def calculate_working_capital(
    sales_revenue,          # 上年度销售收入（万元）
    sales_net_profit_margin,# 上年度销售净利润率（若为负数或极低，银行实务通常取行业微利或0做审慎测算）
    sales_growth_rate,      # 预计销售收入年增长率（例如 0.15 即 15%）
    inventory_turnover_days,# 存货周转天数
    ar_turnover_days,       # 应收账款周转天数
    prepay_turnover_days,   # 预付账款周转天数
    ap_turnover_days,       # 应付账款周转天数
    advance_turnover_days,  # 预收账款/合同负债周转天数
    existing_loans=0.0,     # 现有银行流动资金借款（万元）
    own_funds=0.0           # 自有营运资金及其他渠道资金（万元）
):
    """
    银监会流动资金贷款需求测算公式：
    1. 营运资金周转天数 = 存货周转天数 + 应收账款周转天数 + 预付账款周转天数 - 应付账款周转天数 - 预收账款周转天数
    2. 营运资金周转次数 = 360 / 营运资金周转天数
    3. 营运资金量 = 上年度销售收入 × (1 - 销售利润率) × (1 + 预计销售年增长率) / 营运资金周转次数
    4. 新增流动资金贷款额度 = 营运资金量 - 借款人自有资金 - 现有流动资金贷款 - 其他渠道提供的营运资金
    """
    turnover_days = (
        inventory_turnover_days + 
        ar_turnover_days + 
        prepay_turnover_days - 
        ap_turnover_days - 
        advance_turnover_days
    )
    if turnover_days <= 0:
        turnover_days = 30 # 保护阈值
    
    turnover_times = 360.0 / turnover_days
    
    # 审慎利润率：如果亏损，银行实务一般按 0 或 1%~2% 保守估算以防营运资金虚增
    effective_profit_margin = max(0.0, sales_net_profit_margin)
    
    working_capital_demand = (
        sales_revenue * (1.0 - effective_profit_margin) * (1.0 + sales_growth_rate) / turnover_times
    )
    
    additional_loan_demand = working_capital_demand - own_funds - existing_loans
    
    return {
        "营运资金周转天数": round(turnover_days, 1),
        "营运资金周转次数": round(turnover_times, 2),
        "营运资金量(万元)": round(working_capital_demand, 2),
        "现有借款及自有资金(万元)": round(existing_loans + own_funds, 2),
        "新增流动资金贷款需求额度(万元)": round(additional_loan_demand, 2),
        "测算合规结论": "新增需求充分覆盖申贷金额" if additional_loan_demand > 0 else "新增需求测算饱和"
    }

if __name__ == '__main__':
    # 示例运行（长胜纺织数据）
    res = calculate_working_capital(
        sales_revenue=10479.88,
        sales_net_profit_margin=0.0,
        sales_growth_rate=0.15,
        inventory_turnover_days=137.2,
        ar_turnover_days=362.7,
        prepay_turnover_days=206.1,
        ap_turnover_days=199.6,
        advance_turnover_days=81.3,
        existing_loans=5000.0,
        own_funds=2000.0
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
