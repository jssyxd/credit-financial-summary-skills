#!/usr/bin/env python3
"""财务指标分析表.xlsx 生成器(授信报告(四)同构)。
用法: python indicator_table.py --json audit2023.json audit2024.json audit2025.json audit2606.json \
       --out 本部财务指标分析表.xlsx [--note-period '2026年6月'] [--last-half]
说明: --json 顺序=年份; 末位若为半年/近一期, 流量类(收入/成本/净利分子)按×2年化并标*, 加 --last-half 显式声明。
EBITDA: 附注未披露折旧摊销时按 利润总额+财务费用 列示并在口径注说明(严禁虚构折旧)。
"""
import argparse, json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

_ROMAN = re.compile(r'^[一二三四五六七八九十]+、')


def norm_key(k):
    s = _ROMAN.sub('', str(k)).replace('　', '')
    for p in ('减：', '加：', '其中：', '减:', '加:', '其中:'):
        if s.startswith(p):
            return s[len(p):]
    return s


def g(d, *cs):
    for c in cs:
        for k in d:
            if norm_key(k).startswith(c):
                return d[k]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--period-label', default='2026年6月')
    ap.add_argument('--last-half', action='store_true', help='末期为半年报, 流量按×2年化并标*')
    args = ap.parse_args()
    docs = [json.load(open(p, encoding='utf-8')) for p in args.json]
    half = args.last_half

    def cur(i, tab, *cs):
        return g(docs[i][{'bs': 'bs', 'is': 'is', 'cf': 'cf'}[tab]]['current'], *cs)

    def opn(i, *cs):
        return g(docs[i]['bs']['opening'], *cs)

    wan = lambda v: None if v is None else v / 1e4
    n = len(docs)
    ys = list(range(n))
    TA = [wan(cur(i, 'bs', '资产总计')) for i in ys]
    TL = [wan(cur(i, 'bs', '负债合计')) for i in ys]
    CA = [wan(cur(i, 'bs', '流动资产合计')) for i in ys]
    CL = [wan(cur(i, 'bs', '流动负债合计')) for i in ys]
    INV = [wan(cur(i, 'bs', '存货')) for i in ys]
    CASH = [wan(cur(i, 'bs', '货币资金')) for i in ys]
    TF = [wan(cur(i, 'bs', '交易性金融资产')) for i in ys]
    AR = [wan(cur(i, 'bs', '应收账款') or 0) for i in ys]
    EQ = [wan(cur(i, 'bs', '所有者权益合计') or cur(i, 'bs', '所有者权益（或股东权益）合计') or cur(i, 'bs', '所有者权益（或股东权益)合计')) for i in ys]
    REV = [wan(cur(i, 'is', '营业收入') or 0) for i in ys]
    COST = [wan(cur(i, 'is', '营业成本') or 0) for i in ys]
    NP = [wan(cur(i, 'is', '净利润') or 0) for i in ys]
    TP = [wan(cur(i, 'is', '利润总额') or 0) for i in ys]
    FIN = [wan(cur(i, 'is', '财务费用') or 0) for i in ys]
    STB = [wan(cur(i, 'bs', '短期借款') or 0) for i in ys]
    BP = [wan(cur(i, 'bs', '应付票据') or 0) for i in ys]
    CFO = [wan(cur(i, 'cf', '经营活动产生的现金流量净额') or 0) for i in ys]

    k = [1] * n
    if half:
        k[-1] = 2
    prevTA = wan(opn(0, '资产总计'))
    prevINV = wan(opn(0, '存货'))
    prevAR = wan(opn(0, '应收账款') or 0)
    prevEQ = wan(opn(0, '所有者权益合计') or opn(0, '所有者权益（或股东权益）合计') or opn(0, '所有者权益（或股东权益)合计'))
    star = lambda i: ('*' if half and i == n - 1 else '')

    def fmt(v, i, dp=2):
        return None if v is None else f'{round(v, dp)}{star(i)}'

    out = []
    for i in ys:
        avg = lambda p, c: (p + c) / 2
        rows = []
        rows.append(('资产负债率（%）', None if not TL[i] else round(TL[i] / TA[i] * 100, 2)))
        rows.append(('流动比率', round(CA[i] / CL[i], 2)))
        rows.append(('速动比率', round((CA[i] - INV[i]) / CL[i], 2)))
        rows.append(('利息保障倍数', None if i == n - 1 and half else (round((TP[i] + FIN[i]) / FIN[i], 2) if FIN[i] else None)))
        itr = COST[i] * k[i] / avg(prevINV, INV[i]) if avg(prevINV, INV[i]) else None
        art = REV[i] * k[i] / avg(prevAR, AR[i]) if avg(prevAR, AR[i]) else None
        tat = REV[i] * k[i] / avg(prevTA, TA[i]) if avg(prevTA, TA[i]) else None
        rows.append(('存货周转率（次）', itr))
        rows.append(('应收帐款周转率（次）', art))
        rows.append(('总资产周转率（次）', tat))
        rows.append(('EBITDA（万元）', TP[i] + FIN[i]))   # 口径: 未含折旧摊销(附注未披露时)
        rows.append(('销售净利率（%）', round(NP[i] / REV[i] * 100, 2) if REV[i] else None))
        rows.append(('净资产收益率（%）', round(NP[i] * k[i] / avg(prevEQ, EQ[i]) * 100, 2) if avg(prevEQ, EQ[i]) else None))
        rows.append(('现金比率', round((CASH[i] + TF[i]) / CL[i], 2)))
        rows.append(('经营活动现金净流量／总债务', round(CFO[i] / TL[i], 2) if TL[i] else None))
        rows.append(('经营活动现金净流量／短期债务', round(CFO[i] / (STB[i] + BP[i]), 2) if (STB[i] + BP[i]) else None))
        if i == 0:
            rows += [('销售收入增长率（%）', None), ('净利润增长率（%）', None), ('资本积累率（%）', None)]
        else:
            pREV, pNP, pEQ = REV[i - 1], NP[i - 1], EQ[i - 1]
            gr = (REV[i] / pREV - 1) * 100 if pREV else None
            gnp = (NP[i] - pNP) / abs(pNP) * 100 if pNP else None
            gcap = (EQ[i] - pEQ) / pEQ * 100 if pEQ else None
            rows += [('销售收入增长率（%）', gr), ('净利润增长率（%）', gnp), ('资本积累率（%）', gcap)]
        for name, v in rows:
            out.append((name, v, i))
        prevTA, prevINV, prevAR, prevEQ = TA[i], INV[i], AR[i], EQ[i]

    # 行业均值默认(银行模板常驻参考)
    IND = {'资产负债率（%）': '50-70', '流动比率': '1.5-2.0', '速动比率': '0.8-1.2', '利息保障倍数': '>3',
           '存货周转率（次）': '3-6', '应收帐款周转率（次）': '6-12', '总资产周转率（次）': '0.5-1.0',
           'EBITDA（万元）': '-', '销售净利率（%）': '3-8', '净资产收益率（%）': '8-15', '现金比率': '0.2-0.5',
           '经营活动现金净流量／总债务': '>0.1', '经营活动现金净流量／短期债务': '>0.5',
           '销售收入增长率（%）': '-', '净利润增长率（%）': '-', '资本积累率（%）': '-'}
    CAT = {'资产负债率（%）': '偿债能力', '流动比率': '偿债能力', '速动比率': '偿债能力', '利息保障倍数': '偿债能力',
           '存货周转率（次）': '营运能力', '应收帐款周转率（次）': '营运能力', '总资产周转率（次）': '营运能力',
           'EBITDA（万元）': '盈利能力', '销售净利率（%）': '盈利能力', '净资产收益率（%）': '盈利能力',
           '现金比率': '现金偿还能力', '经营活动现金净流量／总债务': '现金偿还能力', '经营活动现金净流量／短期债务': '现金偿还能力',
           '销售收入增长率（%）': '增长能力', '净利润增长率（%）': '增长能力', '资本积累率（%）': '增长能力'}

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '财务指标分析'
    widths = [12, 30, 11, 11, 11, 12, 12, 20]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.merge_cells('A1:H1')
    ws['A1'] = '财务指标分析表'
    ws['A1'].font = Font(name='仿宋', size=14, bold=True)
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    hdr = ['项目名称', '财务指标'] + [x for x in args.json] + [args.period_label] + ['行业均值(如有)']
    F = lambda sz, b=False: Font(name='仿宋', size=sz, bold=b)
    CA = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin = Side(style='thin', color='000000')
    BD = Border(left=thin, right=thin, top=thin, bottom=thin)
    for c, h in enumerate(hdr, 1):
        cell = ws.cell(3, c, h); cell.font = F(10, True); cell.alignment = CA; cell.border = BD
    seen = set()
    r = 4
    for name, v, i in out:
        if name not in seen:
            seen.add(name)
            ws.cell(r, 1, CAT.get(name, '')).font = F(10)
            ws.cell(r, 2, name).font = F(10)
            ws.cell(r, 8, IND.get(name, '-')).font = F(10)
            for c in (1, 2, 8):
                ws.cell(r, c).alignment = CA if c != 2 else Alignment(horizontal='left', vertical='center')
            for c in range(1, 9):
                ws.cell(r, c).border = BD
            r += 1
        rr = r - 1
        cell = ws.cell(rr, 3 + i)
        if v is None:
            cell.value = '-'
        else:
            cell.value = v
            cell.number_format = '#,##0.00' if abs(v) >= 1000 else ('0.00' if isinstance(v, float) else 'General')
        cell.font = F(10)
        cell.alignment = CA
    note = ('注：①标*为近一期(半年)按×2年化折算；②EBITDA按利润总额+财务费用列示（审计附注未披露折旧摊销时，未含折旧摊销，'
            '与披露折旧的合并口径存在差异）；③利息保障倍数=（利润总额+财务费用）/财务费用，半年期不列示；④现金比率含交易性金融资产；'
            '⑤短期债务=短期借款+应付票据；⑥周转率与ROE用期初期末平均；⑦行业均值取自银行授信制度参考区间，以贵行模板为准。')
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    ws.cell(r, 1, note).font = Font(name='仿宋', size=9)
    ws.cell(r, 1).alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    ws.row_dimensions[r].height = 60
    wb.save(args.out)
    print('saved', args.out)


if __name__ == '__main__':
    main()
