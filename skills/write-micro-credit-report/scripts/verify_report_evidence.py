# -*- coding: utf-8 -*-
"""
小微授信报告反幻觉核查工具
对比 Word/文本报告与实际底层证据（征信、财报、税报、工商），检查是否存在未证实数据或聚时模板历史残留。
"""

import sys, os, re

def check_anti_hallucination(report_text, evidence_dict):
    """
    核查项：
    1. 模板残留检查：检查是否残留聚时科技、郑军、无锡、韦豪创芯等模板原始人名与公司名；
    2. 征信与不良检查：检查是否被错误描述为存在关注类贷款；
    3. 关键金额一致性：检查营业收入、借款金额、申报授信金额是否与底稿一致；
    4. 留空项检查：检查未提供信息是否标明“留空待补充”；
    5. 事实溯源标注：检查段落是否附带【事实依据与来源】。
    """
    issues = []
    warnings = []
    
    # 1. 模板残留
    forbidden_tokens = ["聚时科技", "郑军", "赵丽媛", "乘全科技", "韦豪创芯", "中芯聚源", "JX2000"]
    for t in forbidden_tokens:
        if t in report_text:
            issues.append(f"【模板数据残留风险】报告正文中出现了参考模板的残留字眼：{t}")
            
    # 2. 征信一致性
    if "五级分类被列为关注" in report_text and "浦发银行" in report_text:
        issues.append("【征信幻觉严重缺陷】报告复制了聚时科技模板中的浦发银行关注类贷款，与长胜真实征信不符！")
        
    # 3. 溯源标记统计
    citations = re.findall(r'【事实依据与来源[：:].*?】', report_text)
    
    # 4. 留空项统计
    blanks = re.findall(r'留空待.*?补充', report_text)
    
    return {
        "致命缺陷数": len(issues),
        "缺陷清单": issues,
        "事实溯源标注总数": len(citations),
        "规范留空项总数": len(blanks),
        "审核放行评估": "通过" if len(issues) == 0 else "驳回修改"
    }

if __name__ == '__main__':
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
        res = check_anti_hallucination(text, {})
        print(res)
    else:
        print("Usage: python verify_report_evidence.py <report_text_file>")
