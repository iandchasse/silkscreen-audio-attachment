"""Rasterise build/prev PDF pages for a quick look (CadQuery venv python has PyMuPDF).

    <cq-python> tools/preview.py <pdf> <out_prefix> [x0 x1] (fractions of the page width)
"""
import sys

import pymupdf

d = pymupdf.open(sys.argv[1])
x0, x1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.0, 1.0)
for i, pg in enumerate(d):
    r = pg.rect
    clip = pymupdf.Rect(r.x0 + r.width * x0, r.y0, r.x0 + r.width * x1, r.y1)
    pg.get_pixmap(dpi=int(sys.argv[5]) if len(sys.argv) > 5 else 220, clip=clip).save(f"{sys.argv[2]}_p{i + 1}.png")
print(len(d), "pages")
