"""After gen_schematic.py (MODE "pages"):
  1. export the hierarchical schematic, crop each block's circuit from its page
  2. embed those pictures in the frames of page 1 (KiCad image items, 1:1 scale)
  3. export the final multi-page PDF + one PNG per page
Run with a Python that has PyMuPDF (pip install pymupdf)."""
import base64
import json
import os
import re
import subprocess
import uuid

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
EXP = os.path.join(ROOT, "exports")
SCH = os.path.join(ROOT, "BRC-M400", "BRC-M400.kicad_sch")
PDF = os.path.join(EXP, "BRC-M400_schema.pdf")
DPI = 300
PT = 72 / 25.4


def export():
    subprocess.run([CLI, "sch", "export", "pdf", "-o", PDF, SCH], check=True, capture_output=True)


root_txt = open(SCH, encoding="utf-8").read()
root_txt = re.sub(r"\(image \(at [^\n]*\n", "", root_txt)      # re-runnable: drop old pictures
open(SCH, "w", encoding="utf-8", newline="\n").write(root_txt)
export()

meta = json.load(open(os.path.join(EXP, "pages", "root_images.json")))
doc = pymupdf.open(PDF)
images = []
for m in meta:
    x1, y1, x2, y2 = m["clip"]
    page = doc[m["page"] - 1]
    pix = page.get_pixmap(dpi=DPI, clip=pymupdf.Rect(x1 * PT, y1 * PT, x2 * PT, y2 * PT))
    pix.set_dpi(DPI, DPI)
    png = pix.tobytes("png")
    b64 = base64.b64encode(png).decode()
    chunks = " ".join('"%s"' % b64[i:i + 76] for i in range(0, len(b64), 76))
    dx1, dy1, dx2, dy2 = m["dest"]
    natural_w = pix.width / DPI * 25.4
    scale = (dx2 - dx1) / natural_w
    images.append('(image (at %.4f %.4f) (scale %.6f) (uuid "%s") (data %s))' % (
        (dx1 + dx2) / 2, (dy1 + dy2) / 2, scale, uuid.uuid4(), chunks))
doc.close()

root_txt = root_txt.replace("(sheet_instances", "\n".join(images) + "\n(sheet_instances", 1)
open(SCH, "w", encoding="utf-8", newline="\n").write(root_txt)
export()

doc = pymupdf.open(PDF)
for i, page in enumerate(doc):
    page.get_pixmap(dpi=110 if i == 0 else 150).save(os.path.join(EXP, "BRC-M400_schema_page%d.png" % (i + 1)))
print("pages:", len(doc), "| pictures on page 1:", len(images), "->", PDF)
