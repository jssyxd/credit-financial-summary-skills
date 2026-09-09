import argparse, json, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pymupdf

def parse_pages(s):
    out = []
    for part in s.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-'); out += list(range(int(a), int(b)+1))
        elif part:
            out.append(int(part))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--pages', required=True, help='e.g. 1-33 or 1,3,5-7')
    ap.add_argument('--out', required=True, help='output dir for JSON + png')
    ap.add_argument('--dpi', type=int, default=300)
    ap.add_argument('--noimg', action='store_true')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    doc = pymupdf.open(args.pdf)
    for pno in parse_pages(args.pages):
        if not (1 <= pno <= doc.page_count):
            print(f'skip page {pno} out of range', file=sys.stderr); continue
        page = doc[pno-1]
        zoom = args.dpi/72.0
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY)
        png = os.path.join(args.out, f'p{pno:03d}.png')
        pix.save(png)
        result, _ = engine(png)
        lines = []
        if result:
            for item in result:
                box, text, score = item[0], item[1], item[2]
                pts = [p for p in box]
                x0 = min(p[0] for p in pts); y0 = min(p[1] for p in pts)
                x1 = max(p[0] for p in pts); y1 = max(p[1] for p in pts)
                lines.append({'box': [round(x0), round(y0), round(x1), round(y1)], 'text': text, 'score': round(float(score), 3)})
        with open(os.path.join(args.out, f'p{pno:03d}.json'), 'w', encoding='utf-8') as f:
            json.dump({'page': pno, 'dpi': args.dpi, 'lines': lines}, f, ensure_ascii=False)
        print(f'page {pno}: {len(lines)} lines', flush=True)

if __name__ == '__main__':
    main()
