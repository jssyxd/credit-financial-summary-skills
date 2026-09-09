#!/usr/bin/env python3
"""跨年/跨表一致性校验: 对 extract-financial-statements 产出的 JSON 做
① BS 配平恒等式  ② 跨年连续性(后年期初 == 上年期末)  ③ 单位/期间打印。
用法: python validate_extraction.py --json audit2023.json audit2024.json ... 
允许命名变体(预收账款/预收款项)、口径拆分(应付利息并入其他应付款)等已解释差异——
本脚本只报告差异，解释由人工/Agent 完成。
"""
import argparse, json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

_ROMAN = re.compile(r'^[一二三四五六七八九十]+、')
def nk(k):
    s = _ROMAN.sub('', str(k)).replace('　', '')
    for p in ('减：', '加：', '其中：', '减:', '加:', '其中:'):
        if s.startswith(p):
            return s[len(p):]
    return s

def get(d, *cs):
    for c in cs:
        for k in d:
            if nk(k).startswith(c):
                return d[k]
    return None

def eq_ok(bs):
    ta, tl = bs.get('资产总计'), bs.get('负债合计')
    eqk = None
    for k in bs:
        if (nk(k).startswith('所有者权益合计')
                or nk(k).startswith('所有者权益（或股东权益）合计')
                or nk(k).startswith('所有者权益（或股东权益)合计')):
            eqk = k; break
    if ta is None or tl is None or eqk is None:
        return None
    return abs(ta - (tl + bs[eqk])) <= 1.0

def pairs(a, b, tol=1.0):
    ka, kb = {nk(k): v for k, v in a.items()}, {nk(k): v for k, v in b.items()}
    out = []
    for k in set(ka) | set(kb):
        va, vb = ka.get(k), kb.get(k)
        if va is None or vb is None:
            if (va or 0) != 0 or (vb or 0) != 0:
                out.append((k, va, vb, '单边'))
            continue
        if abs(va - vb) > tol:
            out.append((k, va, vb, round(va - vb, 2)))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', nargs='+', required=True, help='按时间顺序传入 JSON 文件(逗号/空格分隔)')
    args = ap.parse_args()
    docs = [json.load(open(p, encoding='utf-8')) for p in args.json]
    print('== 单位/期间')
    for d in docs:
        print(f'  unit={d.get("unit")} period={d.get("period_end")} pages={d.get("statement_pages")}')
    print('== BS 配平')
    for d in docs:
        cur = d['bs']['current']
        ok = eq_ok(cur)
        ta = cur.get('资产总计')
        print(f'  {d.get("period_end")}: 资产总计={ta} 配平={ "OK" if ok else ("FAIL(缺科目)" if ok is None else "FAIL") }')
    print('== 连续性(后年期初 vs 上年期末)')
    for i in range(len(docs) - 1):
        a, b = docs[i]['bs']['current'], docs[i + 1]['bs']['opening']
        diffs = pairs(a, b)
        print(f'  {docs[i]["period_end"]}末 vs {docs[i+1]["period_end"]}初: '
              + ('OK' if not diffs else f'{len(diffs)}项差异'))
        for k, va, vb, note in diffs[:15]:
            w = lambda v: None if v is None else round(v / 1e4, 2)
            print(f'    {k}: {w(va)} vs {w(vb)} 万元 [{note}]')

if __name__ == '__main__':
    main()
