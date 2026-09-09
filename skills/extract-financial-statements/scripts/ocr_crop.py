import argparse, json, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pymupdf

# Re-OCR a zoomed crop region of a page for ambiguous cells.
# Usage: python ocr_crop.py in.pdf --page 12 --crop x0,y0,x1,y1 --out crop.png [--dpi 500]
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf'); ap.add_argument('--page', type=int, required=True)
    ap.add_argument('--crop', required=True, help='x0,y0,x1,y1 in PDF points')
    ap.add_argument('--out', required=True)
    ap.add_argument('--dpi', type=int, default=500)
    args = ap.parse_args()
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    doc = pymupdf.open(args.pdf)
    page = doc[args.page-1]
    x0, y0, x1, y1 = (float(v) for v in args.crop.split(','))
    zoom = args.dpi/72.0
    clip = pymupdf.Rect(x0, y0, x1, y1)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY, clip=clip)
    pix.save(args.out)
    result, _ = engine(args.out)
    for box, text, score in result:
        print(f'{text}\t{round(float(score),3)}\t{box}')

if __name__ == '__main__':
    main()
