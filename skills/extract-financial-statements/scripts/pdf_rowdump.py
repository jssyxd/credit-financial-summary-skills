#!/usr/bin/env python3
"""文本层 PDF 逐行坐标 dump —— 用于双栏行次制/单栏报表的结构判读与重建。
用法: python pdf_rowdump.py <in.pdf> [--page 1] [--xcut 270]
输出: 每个文本行 y 坐标 + 该行内按 x 排序的 token(带 x 值), 供人工/Agent 判断:
  科目名 | 行次(小整数) | 期末余额 | 年初余额     (资产侧/负债侧由 xcut 分界)
金额列请按 x 升序取 = 期末列 -> 年初列(勿按数值排序)。
"""
import argparse, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pymupdf


def lines_of(page):
    lines = []
    for w in page.get_text('words'):
        x0, y0, x1, y1, t = w[0], w[1], w[2], w[3], w[4]
        yc = (y0 + y1) / 2
        for L in lines:
            if abs(L['yc'] - yc) < 4:
                L['tok'].append((x0, t))
                break
        else:
            lines.append({'yc': yc, 'tok': [(x0, t)]})
    for L in lines:
        L['tok'].sort()
    return sorted(lines, key=lambda L: L['yc'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--page', type=int, default=None, help='只打印某页(1-based), 缺省打印全部')
    ap.add_argument('--xcut', type=float, default=None,
                    help='双栏报表分界x: 打印每行时在 x>=xcut 的token前加竖线标记')
    args = ap.parse_args()
    doc = pymupdf.open(args.pdf)
    pages = [args.page] if args.page else range(1, doc.page_count + 1)
    for pno in pages:
        print(f"\n===== PAGE {pno} =====")
        for L in lines_of(doc[pno - 1]):
            parts, cur = [], []
            for x0, t in L['tok']:
                if args.xcut is not None and x0 >= args.xcut and cur:
                    parts.append('|'.join(cur)); cur = []
                cur.append(f"{x0:6.0f}:{t}")
            if cur:
                parts.append('|'.join(cur))
            print(f"y={L['yc']:7.1f}  " + ' || '.join(parts))


if __name__ == '__main__':
    main()
