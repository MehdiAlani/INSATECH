"""Single-page (flat) schematic composer: every functional block in its own framed section.

Each block is laid out + routed by schem_build.layout_section(); this module packs the blocks
(plus an overview panel) onto one sheet, draws a rounded coloured frame, a title bar and a
notes box per block, then emits the block's circuit centred in its frame.
"""
import itertools
import math
import re

import schem_build

FONT = "Segoe UI"
G = 2.54
# custom page sizes with the A-series ratio, smallest first: the page hugs the content and
# still prints/scales cleanly onto A1 / A2
PAPERS = tuple(sorted((("User", w, h) for w in range(200, 1200, 10) for h in range(140, 900, 10)
                       if 1.3 <= w / h <= 1.6), key=lambda t: t[1] * t[2]))
MARGIN = 15.0          # page edge -> content
BANNER = 24.0          # page title band height
TBLOCK = 40.0          # reserved for KiCad's title block at the bottom
GUT = 3                # cells between frames
PAD = 2                # cells of padding inside a frame
HDR = 4                # title-bar height in cells
NOTE_SIZE = 1.75       # mm, notes font

# name -> (number, title, accent rgb, tint rgb)
STYLE = {
    "overview": ("00", "VUE D'ENSEMBLE  ·  ARCHITECTURE", (38, 50, 56), (244, 246, 248)),
    "power": ("01", "ALIMENTATION  ·  E-Port V2 & convertisseurs", (191, 87, 0), (255, 245, 233)),
    "mcu": ("02", "MICROCONTRÔLEUR  ·  STM32U585 & liaison DJI PSDK", (21, 101, 192), (236, 244, 253)),
    "radio": ("03", "RADIO LoRa  ·  Semtech SX1262 · 868 MHz", (106, 27, 154), (246, 238, 250)),
    "loads": ("04", "ACTIONNEURS DE LARGAGE & SIGNALISATION", (183, 28, 28), (253, 239, 239)),
    "io": ("05", "CAPTEURS & FIXATION", (46, 125, 50), (238, 247, 239)),
}

PRETTY = (("->", "→"), ("<-", "←"), ("+/-", "±"), ("mOhm", "mΩ"), (" Ohm", " Ω"), ("uH", "µH"),
          ("uA", "µA"), ("uF", "µF"), (" us", " µs"), ("!!", "⚠"), (" x ", " × "), ("~", "≈"))


# the design notes are typed in plain ASCII; the page shows proper French
ACCENTS = dict(w.split(":") for w in (
    "detresse:détresse ejection:éjection independants:indépendants securite:sécurité sirene:sirène "
    "alimente:alimenté alimentee:alimentée alimentes:alimentés allumes:allumés barriere:barrière "
    "bouee:bouée cable:câble calibre:calibré coeur:cœur cote:côté defaut:défaut apres:après "
    "demagnetisation:démagnétisation ecrete:écrêté electroaimant:électroaimant energie:énergie "
    "entrees:entrées entree:entrée eteint:éteint ferme:fermé ideale:idéale lacher:lâcher "
    "liberation:libération materielle:matérielle materiels:matériels meme:même precompilee:précompilée "
    "presence:présence rejecteur:réjecteur relie:relié relies:reliés reseau:réseau reference:référence "
    "regionale:régionale sensibilite:sensibilité solenoide:solénoïde verite:vérité surete:sûreté").split())


def _accent(m):
    w = m.group(0)
    if w == "a":
        return "à"
    t = ACCENTS.get(w.lower())
    if not t:
        return w
    if w.isupper() and len(w) > 1:
        return t.upper()
    return t[0].upper() + t[1:] if w[0].isupper() else t


def pretty(s):
    for a, b in PRETTY:
        s = s.replace(a, b)
    return re.sub(r"[A-Za-z]+", _accent, s)


def rgb(c, a=1):
    return "%d %d %d %s" % (c[0], c[1], c[2], a)


def wrap_lines(text, width_mm, size):
    per = max(10, int(width_mm / (0.6 * size)))
    lines, cur = 0, 0
    for word in text.split():
        if cur and cur + 1 + len(word) > per:
            lines += 1
            cur = len(word)
        else:
            cur += (1 if cur else 0) + len(word)
    return lines + 1


def text_w(s, size, bold=False):
    return len(s) * size * (0.66 if bold else 0.6)


class Box:
    """One framed section (a circuit block or the overview panel)."""

    def __init__(self, key, sh=None, cw=0, ch=0, notes=(), min_w_mm=0):
        self.key, self.sh = key, sh
        self.cw, self.ch = cw, ch
        self.notes = [pretty(x) for x in notes if x]
        num, title, acc, tint = STYLE[key]
        self.num, self.title, self.acc, self.tint = num, title.replace("  ·  ", " - ").replace(" · ", " - "), acc, tint
        hdr_w = text_w(num + "  " + title, 3.2, True) + text_w(SUBTITLE.get(key, ""), 2.2) + 22
        self.min_w = max(cw + 2 * PAD, int(math.ceil(max(hdr_w, min_w_mm) / G)) + 2 * PAD)
        self.min_h = HDR + 1 + self.notes_cells(self.min_w) + 1 + ch + PAD

    def notes_mm(self, w_cells):
        if not self.notes:
            return 0.0
        inner = (w_cells - 2 * PAD) * G - 3.0
        lines = sum(wrap_lines("• " + t, inner, NOTE_SIZE) for t in self.notes)
        return lines * NOTE_SIZE * 1.62 + 3.6

    def notes_cells(self, w_cells):
        return int(math.ceil(self.notes_mm(w_cells) / G)) if self.notes else 0


# ---------------------------------------------------------------- packing
def arrangements(boxes):
    """Yield rows = [[column=[box, ...], ...], ...]; a column stacks at most 2 boxes."""
    n = len(boxes)
    for perm in itertools.permutations(boxes):
        for ops in itertools.product((0, 1, 2), repeat=n - 1):   # 0 new col, 1 stack, 2 new row
            rows = [[[perm[0]]]]
            ok = True
            for b, op in zip(perm[1:], ops):
                if op == 0:
                    rows[-1].append([b])
                elif op == 1:
                    if len(rows[-1][-1]) >= 2:
                        ok = False
                        break
                    rows[-1][-1].append(b)
                else:
                    rows.append([[b]])
            if ok:
                yield perm, rows


def measure(rows):
    """Natural size (cells) of an arrangement: row widths and heights."""
    widths, heights = [], []
    for row in rows:
        cols_w = [max(b.min_w for b in col) for col in row]
        cols_h = [sum(b.min_h for b in col) + GUT * (len(col) - 1) for col in row]
        widths.append(sum(cols_w) + GUT * (len(row) - 1))
        heights.append(max(cols_h))
    return widths, heights


def choose_layout(boxes):
    order = {b.key: i for i, b in enumerate(boxes)}
    cands = []
    for perm, rows in arrangements(boxes):
        widths, heights = measure(rows)
        th = sum(heights) + GUT * (len(rows) - 1)
        inner = 0      # wasted area inside frames when columns are stretched to the row height
        for row, rh in zip(rows, heights):
            for col in row:
                ch = sum(b.min_h for b in col) + GUT * (len(col) - 1)
                inner += (rh - ch) * max(b.min_w for b in col)
        inv = sum(1 for i in range(len(perm)) for j in range(i + 1, len(perm))
                  if order[perm[i].key] > order[perm[j].key])
        cands.append((max(widths), th, widths, heights, inner, inv, rows))
    for paper, W, H in PAPERS:
        uw = int((W - 2 * MARGIN) / G)
        uh = int((H - 2 * MARGIN - BANNER - TBLOCK) / G)
        best = None
        for mw, th, widths, heights, inner, inv, rows in cands:
            if mw > uw or th > uh:
                continue
            waste = inner + sum((uw - wdt) * rh for wdt, rh in zip(widths, heights)) + (uh - th) * uw * 0.5
            score = waste + inv * 40
            if best is None or score < best[0]:
                best = (score, rows)
        if best:
            return (paper, W, H), W, H, uw, uh, best[1]
    raise SystemExit("blocks do not fit")


def place(rows, uw, uh, x0, y0):
    """Stretch the arrangement to the usable area; sets b.X, b.Y, b.W, b.H (cells)."""
    widths, heights = measure(rows)
    th = sum(heights) + GUT * (len(rows) - 1)
    extra_v = uh - th
    tot_h = sum(heights)
    y = y0
    for k, (row, rh) in enumerate(zip(rows, heights)):
        rh2 = rh + extra_v * rh // tot_h
        if k == len(rows) - 1:
            rh2 = y0 + uh - y
        cols_w = [max(b.min_w for b in col) for col in row]
        extra_h = uw - (sum(cols_w) + GUT * (len(row) - 1))
        x = x0
        for i, (col, cw) in enumerate(zip(row, cols_w)):
            cw2 = cw + extra_h * cw // sum(cols_w)
            if i == len(row) - 1:
                cw2 = x0 + uw - x
            yy = y
            need = sum(b.min_h for b in col) + GUT * (len(col) - 1)
            spare = rh2 - need
            for j, b in enumerate(col):
                bh = b.min_h + (spare * b.min_h // need if j < len(col) - 1 else 0)
                if j == len(col) - 1:
                    bh = y + rh2 - yy
                b.X, b.Y, b.W, b.H = x, yy, cw2, bh
                yy += bh + GUT
            x += cw2 + GUT
        y += rh2 + GUT


# ---------------------------------------------------------------- drawing
class Draw:
    def __init__(self, M):
        self.M, self.out = M, []

    def rect(self, x1, y1, x2, y2, stroke, width, fill=None, radius=0, dash=False):
        M = self.M
        r = " (radius %s)" % M.n(radius) if radius else ""
        f = "(fill (type color) (color %s))" % rgb(fill) if fill else "(fill (type none))"
        self.out.append('(rectangle (start %s %s) (end %s %s)%s (stroke (width %s) (type %s) (color %s)) %s (uuid %s))' % (
            M.n(x1), M.n(y1), M.n(x2), M.n(y2), r, M.n(width), "dash" if dash else "solid",
            rgb(stroke), f, M.q(M.uid())))

    def poly(self, pts, stroke, width, fill=None):
        M = self.M
        f = "(fill (type color) (color %s))" % rgb(fill) if fill else "(fill (type none))"
        self.out.append('(polyline (pts %s) (stroke (width %s) (type solid) (color %s)) %s (uuid %s))' % (
            ' '.join('(xy %s %s)' % (M.n(x), M.n(y)) for x, y in pts), M.n(width), rgb(stroke), f, M.q(M.uid())))

    def text(self, s, x, y, size, color=None, bold=False, italic=False, just="left", face=None):
        M = self.M
        j = "" if just == "center" else " (justify %s)" % just     # centred is KiCad's default
        self.out.append('(text %s (exclude_from_sim no) (at %s %s 0) (effects (font%s (size %s %s)%s%s%s)%s) '
                        '(uuid %s))' % (
                            M.q(s), M.n(x), M.n(y), " (face %s)" % M.q(face) if face else "", M.n(size), M.n(size),
                            " (bold yes)" if bold else "", " (italic yes)" if italic else "",
                            " (color %s)" % rgb(color) if color else "", j, M.q(M.uid())))

    def textbox(self, s, x, y, w, h, size, color, stroke, fill):
        M = self.M
        self.out.append('(text_box %s (exclude_from_sim no) (at %s %s 0) (size %s %s) (margins 1.8 1.6 1.8 1.6) '
                        '(stroke (width 0.18) (type dash) (color %s)) %s '
                        '(effects (font (face %s) (size %s %s) (color %s)) (justify left top)) (uuid %s))' % (
                            M.q(s).replace("\n", "\\n"), M.n(x), M.n(y), M.n(w), M.n(h), rgb(stroke),
                            "(fill (type color) (color %s))" % rgb(fill) if fill else "(fill (type none))", M.q(FONT),
                            M.n(size), M.n(size), rgb(color), M.q(M.uid())))

    def frame(self, b, right_label="", body_fill=True, box=True, title=True):
        """Plain, hand-drawn look: thin outline, title in KiCad's own font, no fills."""
        M = self.M
        x1, y1 = b.X * G, b.Y * G
        x2, y2 = (b.X + b.W) * G, (b.Y + b.H) * G
        hb = y1 + HDR * G
        if box:
            self.out.append('(rectangle (start %s %s) (end %s %s) (stroke (width 0.25) (type dash)) '
                            '(fill (type none)) (uuid %s))' % (M.n(x1), M.n(y1), M.n(x2), M.n(y2), M.q(M.uid())))
        if title:
            self.text("%s  %s" % (b.num, b.title), x1 + 2.54, y1 + 6.2, 2.54, bold=True)
            if right_label:
                self.text(right_label, x2 - 2.54, y1 + 6.2, 1.5, italic=True, just="right")
        top = hb + G
        if b.notes:
            h = b.notes_mm(b.W)
            self.textbox("\n".join("• " + t for t in b.notes), x1 + PAD * G, top, (b.W - 2 * PAD) * G, h,
                         NOTE_SIZE, (45, 45, 45), b.acc, None)
            top += h + G
        return int(math.ceil(top / G))          # first free cell row


def overview_box(root_notes):
    rows = []
    for line in root_notes[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            rows.append((pretty(k.strip()), pretty(v.strip())))
    b = Box("overview", notes=())
    b.rows = rows
    w = 30 + max(text_w(v, 1.9) for _, v in rows)
    b.diag_h = 44.0
    b.min_w = max(b.min_w, int(math.ceil(max(w, 175) / G)) + 2 * PAD)
    b.min_h = HDR + 1 + int(math.ceil((b.diag_h + 6 + len(rows) * 4.2) / G)) + PAD
    return b


def draw_overview(D, b, sections):
    top_cell = D.frame(b, "Rev C · flux de puissance et de commande")
    x0 = b.X * G + PAD * G
    y = top_cell * G
    inner_w = (b.W - 2 * PAD) * G
    # --- block diagram: E-Port -> Alim -> MCU -> Radio / Actionneurs ; Capteurs -> MCU
    st = {k: STYLE[k] for k in STYLE}
    bw, bh = min(38.0, (inner_w - 4 * 8) / 5), 13.0
    gap = (inner_w - 5 * bw) / 4
    cols = [x0 + i * (bw + gap) for i in range(5)]
    r1, r2 = y + 2, y + 2 + bh + 12
    blocks = [
        ("DJI E-Port V2", "13,8 – 24 V · UART", (90, 90, 90), cols[0], r1),
        ("01 Alimentation", "LM74700 · LMR51430", st["power"][2], cols[1], r1),
        ("02 MCU", "STM32U585 · PSDK", st["mcu"][2], cols[2], r1),
        ("03 Radio LoRa", "SX1262 · 868 MHz", st["radio"][2], cols[3], r1),
        ("05 Capteurs", "verrou · présence", st["io"][2], cols[1], r2),
        ("04 Actionneurs", "aimant · solénoïde · LED", st["loads"][2], cols[3], r2),
    ]
    for t1, t2, c, bx, by in blocks:
        D.rect(bx, by, bx + bw, by + bh, c, 0.4, c, radius=2.0)
        D.text(t1, bx + bw / 2, by + 4.6, 2.3, (255, 255, 255), bold=True, just="center")
        D.text(t2, bx + bw / 2, by + 9.4, 1.6, (255, 255, 255), just="center")
    ant_x = cols[4] + bw / 2

    def arrow(xa, ya, xb, yb, c=(60, 60, 60)):
        D.poly([(xa, ya), (xb, yb)], c, 0.35)
        L = math.hypot(xb - xa, yb - ya)
        ux, uy = (xb - xa) / L, (yb - ya) / L
        s = 1.6
        D.poly([(xb, yb), (xb - s * ux - s * 0.55 * uy, yb - s * uy + s * 0.55 * ux),
                (xb - s * ux + s * 0.55 * uy, yb - s * uy - s * 0.55 * ux), (xb, yb)], c, 0.2, fill=c)

    mid = r1 + bh / 2
    for i in range(3):
        arrow(cols[i] + bw, mid, cols[i + 1], mid)
    # antenna symbol after the radio
    arrow(cols[3] + bw, mid, ant_x - 1, mid, st["radio"][2])
    D.poly([(ant_x, mid + 3), (ant_x, mid - 5)], st["radio"][2], 0.4)
    D.poly([(ant_x - 3, mid - 5), (ant_x, mid - 1), (ant_x + 3, mid - 5), (ant_x - 3, mid - 5)], st["radio"][2], 0.4)
    D.text("antenne 868 MHz", ant_x, mid + 6.5, 1.6, st["radio"][2], italic=True, just="center")
    # capteurs -> MCU, MCU -> actionneurs, alim -> actionneurs (VIN)
    m2 = r2 + bh / 2
    arrow(cols[1] + bw, m2, cols[2] + bw / 2 - 2, m2)
    D.poly([(cols[2] + bw / 2 - 2, m2), (cols[2] + bw / 2 - 2, r1 + bh + 0.3)], (60, 60, 60), 0.35)
    arrow(cols[2] + bw / 2 - 2, m2 - 0.01, cols[2] + bw / 2 - 2, r1 + bh + 0.2)
    D.poly([(cols[2] + bw / 2 + 2, r1 + bh), (cols[2] + bw / 2 + 2, m2)], (60, 60, 60), 0.35)
    arrow(cols[2] + bw / 2 + 2, m2, cols[3], m2)
    D.text("PWM · ARM · mesures I", cols[2] + bw / 2 + 4, m2 - 1.6, 1.4, (80, 80, 80), italic=True)
    for i, lab in enumerate(("VCC", "3V3 · 12V", "SPI · IRQ")):
        D.text(lab, cols[i] + bw + gap / 2, mid - 2.2, 1.4, (80, 80, 80), italic=True, just="center")
    # --- key facts
    yy = r2 + bh + 8
    for k, v in b.rows:
        D.text(k, x0 + 1, yy, 1.9, b.acc, bold=True)
        D.text(v, x0 + 30, yy, 1.9, (40, 40, 40))
        yy += 4.2


# one short line per block, shown in its title bar (no notes paragraphs: the circuit speaks)
SUBTITLE = {
    "power": "24 V E-Port → protection → 3,3 V  +  11,85 V",
    "mcu": "Cortex-M33 · UART PSDK · SWD",
    "radio": "LoRa +22 dBm · TCXO 32 MHz · antenne SMA",
    "loads": "ARM + maintien + éjection + LED + sirène",
    "io": "verrou · présence · fixations M3",
}


def compose(M, sheets, root_notes, counters, inst_path, overview=False, notes=False, subtitle=None):
    """Returns (paper, items). Every sheet already went through schem_build.layout_section()."""
    boxes = [overview_box(root_notes)] if overview else []
    for sh in sheets:
        boxes.append(Box(sh.name, sh, sh.cw, sh.ch, sh.notes if notes else ()))
    paper, W, H, uw, uh, rows = choose_layout(boxes)
    x0 = int(math.ceil(MARGIN / G))
    y0 = int(math.ceil((MARGIN + BANNER) / G))
    place(rows, uw, uh, x0, y0)

    D = Draw(M)
    # page banner
    banner(D, W, subtitle or "Rev C - schema complet")
    # legend of the colour code under the banner line (right part)
    for b in boxes:
        if b.key == "overview":
            draw_overview(D, b, sheets)
            continue
        sh = b.sh
        free = D.frame(b, SUBTITLE.get(sh.name, ""))
        avail = b.Y + b.H - PAD - free
        ox = b.X + (b.W - sh.cw) // 2
        oy = free + max(0, (avail - sh.ch) // 2)
        D.out += schem_build.emit_section(M, sh, ox, oy, counters, inst_path)
        sh.circ_mm = (ox * G, oy * G, (ox + sh.cw) * G, (oy + sh.ch) * G)   # where the circuit sits
    return paper, D.out


def banner(D, W, subtitle):
    D.text("INSATECH", W - MARGIN - 2, MARGIN + 7, 4.0, bold=True, just="right")
    D.text("AeroDay V14 - Challenge CAO", W - MARGIN - 2, MARGIN + 13, 2.0, just="right")


def compose_root(M, sheets, root_uuid):
    """Hierarchical page 1: the same framed layout, each frame body is a clickable sheet symbol
    (double-click -> that block's page). The circuit picture is added later by export_schema_pdf.py
    at the position recorded in sh.root_img_mm."""
    q, n = M.q, M.n
    boxes = [Box(sh.name, sh, sh.cw, sh.ch, ()) for sh in sheets]
    paper, W, H, uw, uh, rows = choose_layout(boxes)
    place(rows, uw, uh, int(math.ceil(MARGIN / G)), int(math.ceil((MARGIN + BANNER) / G)))
    D = Draw(M)
    banner(D, W, "Rev C - vue d'ensemble (double-clic sur un bloc pour ouvrir sa page)")
    for b in boxes:
        sh = b.sh
        free = D.frame(b, box=False, title=False)
        x1, x2 = b.X * G, (b.X + b.W) * G
        y1, y2 = (b.Y + 3) * G, (b.Y + b.H) * G
        D.out.append(
            '(sheet (at %s %s) (size %s %s) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) '
            '(fields_autoplaced no) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) '
            '(uuid %s) '
            '(property "Sheetname" %s (at %s %s 0) (effects (font (size 2.54 2.54) (bold yes)) '
            '(justify left bottom))) '
            '(property "Sheetfile" %s (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left top))) '
            '(instances (project %s (path %s (page %s)))))' % (
                n(x1), n(y1), n(x2 - x1), n(y2 - y1), q(sh.sheet_uuid),
                q("%s  %s" % (b.num, b.title)), n(x1), n(y1 - 1.0),
                q(sh.name + ".kicad_sch"), n(x1), n(y2 + 0.8),
                q(M.PROJECT), q("/" + root_uuid), q(str(sh.page))))
        avail = b.Y + b.H - PAD - free
        ox = b.X + (b.W - sh.cw) // 2
        oy = free + max(0, (avail - sh.ch) // 2)
        sh.root_img_mm = (ox * G, oy * G, (ox + sh.cw) * G, (oy + sh.ch) * G)
    return paper, D.out
