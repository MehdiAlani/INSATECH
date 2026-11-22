# -*- coding: utf-8 -*-
"""Design kit for the INSATECH deck (python-pptx, 16:9)."""
import copy

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# ---------------------------------------------------------------- palette
INK = RGBColor(0x0A, 0x17, 0x24)        # deepest navy, dark slides
NAVY = RGBColor(0x10, 0x29, 0x4A)
NAVY2 = RGBColor(0x16, 0x3B, 0x66)
AMBER = RGBColor(0xFF, 0x7A, 0x1A)      # rescue accent
AMBER_D = RGBColor(0xD9, 0x5F, 0x02)
CYAN = RGBColor(0x2A, 0xC4, 0xD4)
GREEN = RGBColor(0x1E, 0x9E, 0x5A)
RED = RGBColor(0xD1, 0x3A, 0x3A)
VIOLET = RGBColor(0x7B, 0x3F, 0xA8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0x11, 0x20, 0x2E)
MUTED = RGBColor(0x5D, 0x6B, 0x7A)
MUTED_D = RGBColor(0x8F, 0xA6, 0xBC)    # muted on dark
PANEL = RGBColor(0xF2, 0xF6, 0xFA)
HAIR = RGBColor(0xD4, 0xDD, 0xE6)

FONT = "Segoe UI"
FONT_L = "Segoe UI Light"
FONT_SB = "Segoe UI Semibold"

W, H = 13.3333, 7.5          # inches
MG = 0.72                    # side margin


def _set_spacing(run, hundredths):
    """Letter-spacing (python-pptx has no API for it)."""
    run.font._rPr.set("spc", str(int(hundredths)))


def _no_autofit(tf):
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    for tag in ("a:normAutofit", "a:spAutoFit"):
        el = bodyPr.find(qn(tag))
        if el is not None:
            bodyPr.remove(el)


class Slide:
    def __init__(self, prs, dark=False):
        self.prs = prs
        self.s = prs.slides.add_slide(prs.slide_layouts[6])
        self.dark = dark
        if dark:
            self.gradient_bg()
        else:
            self.rect(0, 0, W, H, WHITE, line=None)

    # ---------------------------------------------------------- primitives
    def rect(self, x, y, w, h, fill, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE,
             radius=None):
        sh = self.s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if fill is None:
            sh.fill.background()
        else:
            sh.fill.solid()
            sh.fill.fore_color.rgb = fill
        if line is None:
            sh.line.fill.background()
        else:
            sh.line.color.rgb = line
            sh.line.width = Pt(lw)
        sh.shadow.inherit = False
        if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            sh.adjustments[0] = radius
        sh.text_frame.text = ""
        return sh

    def gradient_bg(self, c1=None, c2=None, angle=5400000):
        sh = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                     Inches(W), Inches(H))
        sh.line.fill.background()
        sh.shadow.inherit = False
        sh.fill.gradient()
        stops = sh.fill.gradient_stops
        stops[0].color.rgb = c1 or INK
        stops[0].position = 0.0
        stops[1].color.rgb = c2 or NAVY
        stops[1].position = 1.0
        sh.fill.gradient_angle = 45.0
        return sh

    def text(self, x, y, w, h, runs, size=14, color=None, bold=False, font=None,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None, line=1.25,
             space_after=0):
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        _no_autofit(tf)
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        if isinstance(runs, str):
            runs = [(runs, {})]
        first = True
        for item in runs:
            if item is None:            # paragraph break
                p = tf.add_paragraph()
                first = False
                continue
            txt, opt = item
            if first:
                p = tf.paragraphs[0]
                first = False
            elif opt.get("newpara"):
                p = tf.add_paragraph()
            p.alignment = opt.get("align", align)
            p.line_spacing = opt.get("line", line)
            p.space_after = Pt(opt.get("space_after", space_after))
            r = p.add_run()
            r.text = txt
            f = r.font
            f.size = Pt(opt.get("size", size))
            f.name = opt.get("font", font or FONT)
            f.bold = opt.get("bold", bold)
            f.italic = opt.get("italic", False)
            f.color.rgb = opt.get("color", color or (WHITE if self.dark else TEXT))
            sp = opt.get("spacing", spacing)
            if sp:
                _set_spacing(r, sp)
        return tb

    def line(self, x1, y1, x2, y2, color=HAIR, lw=1.0):
        from pptx.enum.shapes import MSO_CONNECTOR
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                        Inches(x2), Inches(y2))
        c.line.color.rgb = color
        c.line.width = Pt(lw)
        return c

    def arrow(self, x1, y1, x2, y2, color=MUTED, lw=1.25):
        c = self.line(x1, y1, x2, y2, color, lw)
        ln = c.line._get_or_add_ln()
        tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
        ln.append(tail)
        return c

    def picture(self, path, x, y, w=None, h=None):
        return self.s.shapes.add_picture(path, Inches(x), Inches(y),
                                         Inches(w) if w else None, Inches(h) if h else None)

    def picture_fit(self, path, x, y, w, h, align="center"):
        """Place preserving aspect, contained in the box."""
        from PIL import Image
        iw, ih = Image.open(path).size
        sc = min(w / iw, h / ih)
        pw, ph = iw * sc, ih * sc
        px = x + (w - pw) / 2 if align == "center" else x
        return self.picture(path, px, y + (h - ph) / 2, pw, ph)

    # ---------------------------------------------------------- components
    def kicker(self, txt, x=MG, y=0.62, color=None):
        self.text(x, y, 8, 0.26, [(txt.upper(), {})], size=10.5,
                  color=color or (CYAN if self.dark else AMBER_D), bold=True, spacing=180)

    def title(self, txt, x=MG, y=0.92, size=30, w=None, color=None):
        self.text(x, y, w or (W - 2 * MG), 1.0, [(txt, {})], size=size,
                  color=color or (WHITE if self.dark else NAVY), bold=True, line=1.1)

    def rule(self, y=1.72, color=None, x1=MG, x2=None):
        self.line(x1, y, x2 or (W - MG), y, color or (RGBColor(0x24, 0x40, 0x60) if self.dark else HAIR), 1.0)

    def accent_bar(self, x=MG, y=1.60, w=1.15, color=AMBER, h=0.055):
        self.rect(x, y, w, h, color)

    def chip(self, x, y, w, h, title, sub=None, fill=NAVY, tcolor=WHITE, size=13, sub_size=9.5):
        self.rect(x, y, w, h, fill)
        runs = [(title, {"size": size, "bold": True, "color": tcolor, "align": PP_ALIGN.CENTER})]
        if sub:
            runs.append((sub, {"newpara": True, "size": sub_size, "bold": False,
                               "color": tcolor, "align": PP_ALIGN.CENTER}))
        self.text(x, y, w, h, runs, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)

    def stat(self, x, y, w, value, label, color=None, size=40, lsize=10):
        self.text(x, y, w, 0.75, [(value, {})], size=size, color=color or AMBER,
                  bold=True, font=FONT, line=1.0)
        self.text(x, y + 0.62, w, 0.5, [(label, {})], size=lsize,
                  color=MUTED_D if self.dark else MUTED, line=1.2)

    def footer(self, n):
        c = RGBColor(0x45, 0x5A, 0x70) if self.dark else RGBColor(0x9A, 0xA7, 0xB4)
        self.text(MG, H - 0.52, 8, 0.3,
                  [("INSATECH  ·  BRC-M400 Rev C  ·  AeroDay V14 — Challenge CAO", {})],
                  size=8.5, color=c)
        self.text(W - MG - 1.2, H - 0.52, 1.2, 0.3, [(str(n), {})], size=8.5,
                  color=c, align=PP_ALIGN.RIGHT)


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Inches(W)
        self.prs.slide_height = Inches(H)
        self.slides = []

    def add(self, dark=False):
        s = Slide(self.prs, dark)
        self.slides.append(s)
        return s

    def save(self, path, skip_footer=(1,)):
        for i, s in enumerate(self.slides, 1):
            if i not in skip_footer:
                s.footer(i)
        self.prs.save(path)
        print("pptx: %d slides -> %s" % (len(self.slides), path))
        return path
