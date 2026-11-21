# -*- coding: utf-8 -*-
"""Slide toolkit (16:9, PyMuPDF) for the INSATECH pitch deck."""
import os

import pymupdf

import style as S

W, H = 960.0, 540.0
M = 46.0                      # side margin
NAVY = (0.071, 0.208, 0.357)
BLUE = (0.084, 0.396, 0.753)
ORANGE = (0.749, 0.341, 0.0)
GREEN = (0.106, 0.369, 0.125)
DARK = (0.055, 0.102, 0.149)
INK = (0.098, 0.133, 0.169)
GREY = (0.353, 0.400, 0.447)
HAIR = (0.788, 0.824, 0.855)
PAPER = (1, 1, 1)

SLIDE_CSS = S.FACE + """
body {font-family: sg; font-size: 13px; color: #19222B; line-height: 1.42;}
p {margin: 0 0 7px 0;}
ul {margin: 0 0 6px 0; padding-left: 15px;}
li {margin: 0 0 5px 0;}
b {color: #0D1117;}
.big {font-size: 27px; font-weight: bold; color: #12355B; line-height: 1.12;}
.num {font-size: 30px; font-weight: bold; color: #1565C0;}
.unit {font-size: 12px; color: #5A6672;}
.cap {font-size: 10.5px; color: #5A6672;}
.k {font-size: 11.5px; color: #5A6672;}
.hi {color: #BF5700; font-weight: bold;}
.ok {color: #1B5E20; font-weight: bold;}
.todo {color: #BF5700; font-style: italic;}
small {font-size: 10.5px; color: #5A6672;}
"""


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


class Deck:
    def __init__(self, path):
        self.doc = pymupdf.open()
        self.path = path
        self.arch = pymupdf.Archive(S.FONTS)
        self.n = 0

    def slide(self, title=None, kicker=None, dark=False):
        pg = self.doc.new_page(width=W, height=H)
        self.n += 1
        pg.draw_rect(pymupdf.Rect(0, 0, W, H), color=None, fill=DARK if dark else PAPER)
        self.cur_dark = dark
        y = 58
        if kicker:
            self.html(pymupdf.Rect(M, 40, W - M, 60),
                      '<span style="font-size:11.5px;letter-spacing:.5px;color:%s">%s</span>'
                      % ("#8FA6BC" if dark else "#1565C0", kicker.upper()), pg)
            y = 72
        if title:
            self.html(pymupdf.Rect(M, y, W - M, y + 46),
                      '<span style="font-size:25px;font-weight:bold;color:%s">%s</span>'
                      % ("#FFFFFF" if dark else "#12355B", title), pg)
            pg.draw_line(pymupdf.Point(M, y + 46), pymupdf.Point(W - M, y + 46),
                         color=hx("#2A3F55") if dark else HAIR, width=0.8)
        self.page = pg
        return pg

    def html(self, rect, body, pg=None, css=None, align_mid=False):
        pg = pg or self.page
        pg.insert_htmlbox(rect, body, css=(css or SLIDE_CSS), archive=self.arch,
                          scale_low=0.55)

    def image(self, rect, path, pad=0, frame=True, dark_panel=False):
        pg = self.page
        if dark_panel:
            pg.draw_rect(rect, color=None, fill=hx("#0B131B"))
        elif frame:
            pg.draw_rect(rect, color=HAIR, fill=hx("#FCFDFE"), width=0.7)
        inner = rect + (pad, pad, -pad, -pad)
        pg.insert_image(inner, filename=path, keep_proportion=True)

    def panel(self, rect, fill="#F4F7FA", border=None, radius=None):
        self.page.draw_rect(rect, color=hx(border) if border else None, fill=hx(fill),
                            width=0.8 if border else 0)

    def chip(self, x, y, w, h, text, fill, tcolor="#FFFFFF", size=12.5, bold=True):
        r = pymupdf.Rect(x, y, x + w, y + h)
        self.page.draw_rect(r, color=None, fill=hx(fill) if isinstance(fill, str) else fill)
        self.html(r + (4, (h - size * 1.9) / 2, -4, 0),
                  '<div style="text-align:center;font-size:%.1fpx;color:%s;%s">%s</div>'
                  % (size, tcolor, "font-weight:bold;" if bold else "", text))
        return r

    def arrow(self, x1, y1, x2, y2, color=None, width=1.4, head=7.0):
        import math
        pg = self.page
        c = color or GREY
        pg.draw_line(pymupdf.Point(x1, y1), pymupdf.Point(x2, y2), color=c, width=width)
        a = math.atan2(y2 - y1, x2 - x1)
        for s in (2.6, -2.6):
            pg.draw_line(pymupdf.Point(x2, y2),
                         pymupdf.Point(x2 - head * math.cos(a - s / 6), y2 - head * math.sin(a - s / 6)),
                         color=c, width=width)

    def footer(self):
        for i, pg in enumerate(self.doc):
            if i == 0:
                continue
            dark = pg.get_pixmap(clip=pymupdf.Rect(2, 2, 4, 4)).pixel(0, 0)[0] < 120
            col = "#7F8C99" if not dark else "#5B6C7D"
            pg.insert_htmlbox(
                pymupdf.Rect(M, H - 30, W - M, H - 10),
                '<table style="width:100%%;border-collapse:collapse"><tr>'
                '<td style="border:none;padding:0;font-size:10px;color:%s">INSATECH &middot; '
                'BRC-M400 Rev C &middot; AeroDay V14 — Challenge CAO</td>'
                '<td style="border:none;padding:0;text-align:right;font-size:10px;color:%s">%d</td>'
                '</tr></table>' % (col, col, i + 1),
                css=SLIDE_CSS, archive=self.arch)

    def save(self):
        self.footer()
        self.doc.subset_fonts()
        self.doc.save(self.path, garbage=4, deflate=True)
        print("deck: %d slides -> %s" % (len(self.doc), self.path))
        return self.doc
