"""
BRC-M400 PCB generator (KiCad 10 pcbnew API).

Builds BRC-M400.kicad_pcb from the KiCad netlist exported from the schematic:
4-layer stackup, rounded outline, zoned placement, GND planes, stitching vias,
silkscreen. Footprints carry the schematic symbol paths, so "Update PCB from
Schematic" (F8) in the GUI matches them instead of duplicating.

Usage (KiCad's bundled Python):
    kicad-cli sch export netlist --format kicadsexpr -o ../exports/BRC-M400.net ../BRC-M400/BRC-M400.kicad_sch
    python.exe gen_pcb.py

Tracks are NOT routed: placement + planes only. Route signals in the GUI.
"""
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sexp import load, head  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, ".."))
NETLIST = os.path.join(ROOT, "exports", "BRC-M400.net")
PCB = os.path.join(ROOT, "BRC-M400", "BRC-M400.kicad_pcb")
FPDIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"

W, H = 96.0, 66.0          # board size, mm
OX, OY = 100.0, 100.0      # board origin on the KiCad canvas
CLEAR = 0.45               # courtyard-to-courtyard spacing used by the packer
HOLE_XY = [(3.6, 3.6), (W - 3.6, 3.6), (3.6, H - 3.6), (W - 3.6, H - 3.6)]

MM = pcbnew.FromMM


def P(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))


# ---------------------------------------------------------------------------
# Placement plan.  Regions are (x0, y0, x1, y1) in board mm.
# fixed: ref -> (x, y, rotation_deg)   others are packed near the anchor.
# ---------------------------------------------------------------------------
REGIONS = {
    "pwr":   (0.5, 7.5, 22.0, 29.0),
    "buck":  (0.5, 29.0, 30.0, 58.5),
    "mcu":   (22.0, 0.5, 54.0, 29.0),
    "radio": (54.0, 0.5, 95.5, 29.0),
    "act":   (30.0, 29.0, 95.5, 50.2),
}

GROUPS = [
    # name, region, anchor ref, members (placement order = priority)
    ("pwr", "pwr", "Q1", ["U1", "C1", "C2", "D1", "F1", "R7", "R8", "C20"]),
    ("mcu", "mcu", "U10", ["C30", "C31", "C32", "C33", "C34", "C35", "C36", "C37", "R10", "X1", "C38", "C39",
                           "R14", "R15", "D10", "R11", "R12", "R13",
                           "R60", "R61", "R62", "R63", "C90", "C91"]),
    ("radio", "radio", "U20", ["C50", "C51", "C52", "C53", "C54", "L20", "Y20", "FB20", "C55", "C56", "R20",
                               "C57", "C58", "R21", "C67", "R22", "C68", "FB1", "C16", "C17"]),
    ("buck3", "buck", "U3", ["C11", "C12", "C13", "R4", "R5", "R6", "C14", "C15", "U4", "C19"]),
    ("ldo", "buck", "U2", ["C4", "C5", "C6", "C7", "R1", "R2"]),
    ("arm", "act", "Q30", ["R30", "R33", "Q31", "R34", "R35", "C80", "C81"]),
    ("hold", "act", "Q34", ["C87", "R46", "R47", "R48", "R49", "U30", "C88", "R36", "C82", "D32", "D33"]),
    ("eject", "act", "Q35", ["C89", "R51", "R52", "R53", "R54", "U36", "C92", "R37", "C93", "D34", "D35"]),
    ("led", "act", "Q32", ["C83", "R38", "R31", "R32", "R39", "D30", "U32", "C84", "R41", "C85"]),
    ("siren", "act", "Q33", ["C86", "R42", "R43", "R44", "R45", "D31"]),
]

FIXED = {
    # power input column: XT30 male, plug face 1 mm proud of the left edge
    "J1": (12.1, 13.0, 90), "Q1": (17.5, 26.0, 0),
    # bulk + converters (left, lower half)
    "C3": (13.0, 52.5, 0), "U3": (7.5, 34.0, 0), "L2": (15.5, 37.5, 0), "U2": (24.5, 40.0, 0),
    # MCU + signal connectors on the top edge
    "U10": (36.0, 15.5, 0), "J7": (27.5, 4.5, 90),
    "J2": (44.0, 3.2, 180), "J6": (66.0, 3.2, 180),
    # radio, SMA on the right edge
    "U20": (61.0, 15.0, 0), "U21": (82.0, 15.0, 0), "J20": (W - 3.2, 15.0, 0),
    # ARM switch between the two coil channels
    "Q30": (62.0, 33.5, 0), "U33": (71.0, 32.5, 0),
    # power channels: driver above MOSFET above XT30 (bottom edge), shunt beside the MOSFET
    "U31": (37.0, 38.5, 0), "Q32": (37.0, 44.0, 0), "R40": (43.5, 44.0, 90), "J31": (40.0, 52.9, 180),
    "U34": (52.5, 38.5, 0), "Q34": (53.0, 44.0, 0), "R50": (59.5, 44.0, 90), "J33": (56.0, 52.9, 180),
    "U35": (69.0, 38.5, 0), "Q35": (69.0, 44.0, 0), "R55": (75.5, 44.0, 90), "J34": (72.0, 52.9, 180),
    # siren: XT30 on the right edge
    "Q33": (76.0, 35.0, 90), "J32": (W + 1.0 - 14.1, 33.0, 270),
}

# RF chain laid out in signal order between SX1262 and the switch
RF_TX_ROW = ["L22", "C59", "L21", "L23", "C60", "C61", "C62", "L24", "C63"]
RF_RX_ROW = ["C64", "L25", "C66", "C65"]
RF_ANT_ROW = ["C69", "C70", "R23", "C71"]

STD3D = "${KICAD10_3DMODEL_DIR}/"
MODEL_OVERRIDE = {
    "U10": STD3D + "Package_DFN_QFN.3dshapes/QFN-48-1EP_7x7mm_P0.5mm_EP5.15x5.15mm.step",
    "Q30": STD3D + "Package_TO_SOT_SMD.3dshapes/TDSON-8-1.step",
    "Y20": STD3D + "Crystal.3dshapes/Crystal_SMD_2520-4Pin_2.5x2.0mm.step",
    "J1": "${KIPRJMOD}/3d/XT30PW-M.wrl",
    "J31": "${KIPRJMOD}/3d/XT30PW-F.wrl",
    "J32": "${KIPRJMOD}/3d/XT30PW-F.wrl",
    "J33": "${KIPRJMOD}/3d/XT30PW-F.wrl",
    "J34": "${KIPRJMOD}/3d/XT30PW-F.wrl",
    "U2": STD3D + "Package_SO.3dshapes/MSOP-8-1EP_3x3mm_P0.65mm_EP2.5x3mm_Mask1.73x2.36mm.step",
}

HIDE_REF_PREFIX = ("C", "R", "L", "FB")   # passives: no silkscreen reference
HIDE_REF = {"J1", "J2", "J6", "J7", "J20", "J31", "J32", "J33", "J34"}   # connectors carry a function label instead


# ---------------------------------------------------------------------------
def parse_netlist(path):
    root = load(path)
    comps, nets = {}, {}
    for sec in root:
        if head(sec) == 'components':
            for comp in sec[1:]:
                d = {}
                for f in comp[1:]:
                    h = head(f)
                    if h in ('ref', 'value', 'footprint'):
                        d[h] = f[1][1]
                    elif h == 'sheetpath':
                        for g in f[1:]:
                            if head(g) == 'tstamps':
                                d['sheet'] = g[1][1]
                    elif h in ('tstamps', 'tstamp'):
                        d['uuid'] = f[1][1]
                    elif h == 'property' and f[1][1] == 'dnp':
                        d['dnp'] = True
                comps[d['ref']] = d
        if head(sec) == 'nets':
            for net in sec[1:]:
                name = None
                for f in net[1:]:
                    if head(f) == 'name':
                        name = f[1][1]
                    elif head(f) == 'node':
                        ref = pin = None
                        for g in f[1:]:
                            if head(g) == 'ref':
                                ref = g[1][1]
                            elif head(g) == 'pin':
                                pin = g[1][1]
                        nets[(ref, pin)] = name
    return comps, nets


def short_net(name):
    # "/Sheet/LOCAL" -> keep KiCad's full name (unique), globals are bare
    return name


def fp_bbox(fp):
    """Courtyard bbox in mm (absolute), falling back to the body bbox."""
    try:
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() > 0:
            b = cy.BBox()
            return (pcbnew.ToMM(b.GetLeft()) - OX, pcbnew.ToMM(b.GetTop()) - OY,
                    pcbnew.ToMM(b.GetRight()) - OX, pcbnew.ToMM(b.GetBottom()) - OY)
    except Exception:
        pass
    b = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(b.GetLeft()) - OX, pcbnew.ToMM(b.GetTop()) - OY,
            pcbnew.ToMM(b.GetRight()) - OX, pcbnew.ToMM(b.GetBottom()) - OY)


def overlaps(a, b, c=CLEAR):
    return not (a[2] + c <= b[0] or b[2] + c <= a[0] or a[3] + c <= b[1] or b[3] + c <= a[1])


class Placer:
    def __init__(self):
        self.boxes = {}
        # keep-outs: mounting holes
        for i, (x, y) in enumerate(HOLE_XY):
            self.boxes["_hole%d" % i] = (x - 3.4, y - 3.4, x + 3.4, y + 3.4)

    def free(self, box, ignore=None):
        if box[0] < 0.4 or box[1] < 0.4 or box[2] > W - 0.4 or box[3] > H - 0.4:
            return False
        return all(not overlaps(box, b) for k, b in self.boxes.items() if k != ignore)

    def put(self, fp, x, y, rot=0.0, check=True):
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(P(x, y))
        box = fp_bbox(fp)
        if check and not self.free(box):
            return False
        self.boxes[fp.GetReference()] = box
        return True

    def near(self, fp, cx, cy, region, rot=0.0):
        """Spiral search for the closest free spot to (cx, cy) inside region."""
        x0, y0, x1, y1 = region
        for rr in (rot, rot + 90):
            fp.SetOrientationDegrees(rr)
            for radius in [i * 0.5 for i in range(0, 80)]:
                steps = max(8, int(2 * math.pi * radius / 0.5))
                for k in range(steps):
                    a = 2 * math.pi * k / steps
                    x, y = cx + radius * math.cos(a), cy + radius * math.sin(a)
                    fp.SetPosition(P(x, y))
                    b = fp_bbox(fp)
                    if b[0] < x0 or b[1] < y0 or b[2] > x1 or b[3] > y1:
                        continue
                    if self.free(b):
                        self.boxes[fp.GetReference()] = b
                        return True
        return False


def add_outline(board):
    r = 3.0
    lw = MM(0.1)

    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(lw)
        board.Add(s)

    def arc(start, mid, end):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(P(*start), P(*mid), P(*end))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(lw)
        board.Add(s)

    k = r * (1 - math.cos(math.radians(45)))
    seg((r, 0), (W - r, 0))
    arc((W - r, 0), (W - k, k), (W, r))
    seg((W, r), (W, H - r))
    arc((W, H - r), (W - k, H - k), (W - r, H))
    seg((W - r, H), (r, H))
    arc((r, H), (k, H - k), (0, H - r))
    seg((0, H - r), (0, r))
    arc((0, r), (k, k), (r, 0))


def add_text(board, txt, x, y, size, layer=pcbnew.F_SilkS, thick=None, mirror=False, bold=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(thick if thick else size * 0.15))
    if bold:
        t.SetBold(True)
    if mirror:
        t.SetMirrored(True)
    board.Add(t)
    return t


def add_zone(board, net, layer, pts, prio=0, clearance=0.3):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(net.GetNetCode())
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(clearance))
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.35))
    try:
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    except Exception:
        pass
    ol = z.Outline()
    ol.NewOutline()
    for (x, y) in pts:
        ol.Append(MM(OX + x), MM(OY + y))
    board.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def set_model(fp, path):
    models = fp.Models()
    if len(models):
        models[0].m_Filename = path
        models[0].m_Show = True
    else:
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = path
        m.m_Show = True
        models.push_back(m)


def write_xt30_models():
    """XT30 right-angle PCB connectors have no 3D model in the KiCad library:
    write simple but dimensionally faithful VRML models (units: 0.1 inch)."""
    out = os.path.join(ROOT, "BRC-M400", "3d")
    os.makedirs(out, exist_ok=True)
    yellow = (0.96, 0.77, 0.10)
    dark = (0.07, 0.07, 0.07)
    gold = (0.86, 0.66, 0.26)

    def box(x0, x1, y0, y1, z0, z1, col):
        # footprint coords (mm, y down) -> VRML (0.1 in, y up)
        cx, cy, cz = (x0 + x1) / 2 / 2.54, -(y0 + y1) / 2 / 2.54, (z0 + z1) / 2 / 2.54
        sx, sy, sz = abs(x1 - x0) / 2.54, abs(y1 - y0) / 2.54, abs(z1 - z0) / 2.54
        return ("Transform { translation %.4f %.4f %.4f children [ Shape { appearance Appearance { "
                "material Material { diffuseColor %.3f %.3f %.3f specularColor 0.35 0.35 0.35 shininess 0.35 } } "
                "geometry Box { size %.4f %.4f %.4f } } ] }\n") % (cx, cy, cz, col[0], col[1], col[2], sx, sy, sz)

    def model(pins, base, shroud, ears):
        parts = []
        bx0, bx1, by0, by1 = base
        parts.append(box(bx0, bx1, by0, by1, 0.0, 5.2, yellow))
        sx0, sx1, sy0, sy1 = shroud
        parts.append(box(sx0, sx1, sy0, sy1, 0.15, 5.05, yellow))
        for px in pins:
            parts.append(box(px - 1.65, px + 1.65, sy0 - 0.06, sy0 + 0.4, 1.1, 4.1, dark))
            parts.append(box(px - 0.55, px + 0.55, sy0 - 0.1, sy0 + 0.2, 2.0, 3.2, gold))
            parts.append(box(px - 0.5, px + 0.5, by1 - 0.2, 0.7, 0.0, 0.9, gold))
        for (ex, ey) in ears:
            parts.append(box(ex - 0.8, ex + 0.8, ey - 1.0, ey + 1.0, 0.0, 0.35, gold))
        return "#VRML V2.0 utf8\n" + "".join(parts)

    with open(os.path.join(out, "XT30PW-M.wrl"), "w") as f:
        f.write(model([0.0, -5.0], (-7.5, 2.5, -9.0, -4.1), (-7.5, 2.5, -13.1, -9.0),
                      [(-8.0, -10.0), (3.0, -10.0)]))
    with open(os.path.join(out, "XT30PW-F.wrl"), "w") as f:
        f.write(model([0.0, 5.0], (-2.5, 7.5, -8.1, -4.0), (-1.97, 6.97, -14.1, -8.1),
                      [(-3.0, -5.0), (8.0, -5.0)]))


STACKUP = """    (stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 2" (type "core") (thickness 1.04) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )
"""


def patch_stackup(path):
    """Write a real 4-layer stackup (matte black mask, ENIG) into the board file."""
    txt = open(path, encoding="utf-8").read()
    if "(stackup" in txt:
        return
    i = txt.find("(setup")
    j = txt.find("\n", i)
    txt = txt[:j + 1] + STACKUP + txt[j + 1:]
    open(path, "w", encoding="utf-8", newline="\n").write(txt)


def write_project_rules():
    """Fab-realistic rules (4-layer, 0.1 mm capable) and routing net classes."""
    import json
    pro = os.path.join(ROOT, "BRC-M400", "BRC-M400.kicad_pro")
    try:
        d = json.load(open(pro, encoding="utf-8"))
    except Exception:
        d = {"meta": {"filename": "BRC-M400.kicad_pro", "version": 3}}
    rules = d.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
    rules.update({"min_clearance": 0.1, "min_track_width": 0.1, "min_through_hole_diameter": 0.2,
                  "min_via_diameter": 0.4, "min_via_annular_width": 0.1, "min_hole_clearance": 0.2,
                  "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3, "min_text_height": 0.8,
                  "min_text_thickness": 0.12})

    def nc(name, clr, tw, via=0.6, drill=0.3):
        return {"name": name, "clearance": clr, "track_width": tw, "via_diameter": via, "via_drill": drill,
                "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
                "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}
    ns = d.setdefault("net_settings", {})
    ns["classes"] = [nc("Default", 0.15, 0.2), nc("POWER", 0.15, 1.0, 0.8, 0.4), nc("RF50", 0.2, 0.36)]
    ns["netclass_patterns"] = (
        [{"netclass": "POWER", "pattern": pt} for pt in
         ("VIN", "*VIN_RAW", "*VIN_F", "V_ACT", "*HOLD_N", "*EJ_N", "*LEDA_N", "*SIREN_N", "*_SRC",
          "*HOLD_K", "*EJ_K", "*SW_3V3")] +
        [{"netclass": "RF50", "pattern": pt} for pt in
         ("*RFO", "*RF_A", "*RF_B", "*RF_C", "*RF_TXP", "*RF_RXP", "*RF_ANT", "*RF_ANT2", "*RF_OUT")])
    ns.setdefault("meta", {"version": 4})
    with open(pro, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=2)


def set_stackup_colors(board):
    """Matte black soldermask + white silk if the API allows (cosmetic)."""
    try:
        ds = board.GetDesignSettings()
        ds.m_HasStackup = True
        stk = ds.GetStackupDescriptor()
        for it in stk.GetList():
            name = it.GetTypeName()
            if "Solder Mask" in name:
                it.SetColor("Black")
            elif "Silk Screen" in name:
                it.SetColor("White")
        return True
    except Exception as e:  # noqa: BLE001
        print("  (stackup colours not set: %s)" % e)
        return False


def main():
    write_xt30_models()
    comps, pinnet = parse_netlist(NETLIST)
    board = pcbnew.NewBoard(PCB)
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))

    # nets
    netobj = {}
    for name in sorted(set(pinnet.values())):
        if name.startswith("unconnected-"):
            continue
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netobj[name] = ni

    # footprints
    fps = {}
    for ref, d in sorted(comps.items()):
        if not d.get('footprint'):
            continue
        lib, name = d['footprint'].split(':', 1)
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
        if fp is None:
            print("!! footprint not found", d['footprint'])
            continue
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(d.get('value', ''))
        if d.get('sheet') and d.get('uuid'):
            fp.SetPath(pcbnew.KIID_PATH(d['sheet'] + d['uuid']))
        if d.get('dnp'):
            try:
                fp.SetDNP(True)
            except Exception:
                pass
        # assign nets by pad number
        missing = []
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                continue
            net = pinnet.get((ref, num))
            if net and net in netobj:
                pad.SetNet(netobj[net])
            elif (ref, num) not in pinnet and num not in ("MP",):
                missing.append(num)
        if missing:
            print("  note %s: pads without symbol pin %s" % (ref, sorted(set(missing))))
        # silkscreen reference policy
        refl = fp.Reference()
        refl.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        refl.SetTextThickness(MM(0.12))
        if ref in HIDE_REF or ref.startswith(HIDE_REF_PREFIX):
            refl.SetVisible(False)
        fp.Value().SetVisible(False)
        if ref in MODEL_OVERRIDE:
            set_model(fp, MODEL_OVERRIDE[ref])
        board.Add(fp)
        fps[ref] = fp

    pl = Placer()
    placed = set()

    def place_fixed(ref, x, y, rot):
        if ref in fps:
            pl.put(fps[ref], x, y, rot, check=False)
            placed.add(ref)

    for ref, (x, y, rot) in FIXED.items():
        place_fixed(ref, x, y, rot)

    # mounting holes
    for i, (x, y) in enumerate(HOLE_XY):
        ref = "H%d" % (i + 1)
        if ref in fps:
            fps[ref].SetPosition(P(x, y))
            placed.add(ref)

    # RF rows
    def row(refs, x, y, step):
        for r_ in refs:
            if r_ in fps:
                fps[r_].SetOrientationDegrees(90)
                pl.put(fps[r_], x, y, 90, check=False)
                placed.add(r_)
                x += step
    row(RF_TX_ROW, 65.0, 10.5, 1.25)
    row(RF_RX_ROW, 68.5, 20.0, 1.25)
    row(RF_ANT_ROW, 84.6, 10.8, 1.25)

    # groups
    for gname, region, anchor, members in GROUPS:
        reg = REGIONS[region]
        a = fps[anchor]
        ax, ay = pcbnew.ToMM(a.GetPosition().x) - OX, pcbnew.ToMM(a.GetPosition().y) - OY
        for ref in members:
            if ref in placed or ref not in fps:
                continue
            if not pl.near(fps[ref], ax, ay, reg):
                # fallback: anywhere on the board
                if not pl.near(fps[ref], ax, ay, (0.5, 0.5, W - 0.5, H - 0.5)):
                    print("!! could not place", ref)
            placed.add(ref)

    # anything left
    for ref, fp in fps.items():
        if ref not in placed:
            if not pl.near(fp, W / 2, H / 2, (0.5, 0.5, W - 0.5, H - 0.5)):
                print("!! could not place", ref)
            else:
                print("  placed leftover", ref)

    add_outline(board)

    # ---- planes
    gnd = netobj["GND"]
    add_zone(board, gnd, pcbnew.In1_Cu, rect(0, 0, W, H), prio=0)
    add_zone(board, gnd, pcbnew.F_Cu, rect(0, 0, W, H), prio=0)
    add_zone(board, gnd, pcbnew.B_Cu, rect(0, 0, W, H), prio=0)
    # In2: split power plane
    add_zone(board, netobj["+3V3"], pcbnew.In2_Cu, rect(22.4, 0.4, W - 0.4, 28.6), prio=1)
    add_zone(board, netobj["VIN"], pcbnew.In2_Cu, rect(0.4, 0.4, 21.6, 28.6), prio=1)
    add_zone(board, netobj["VIN"], pcbnew.In2_Cu, rect(0.4, 29.4, W - 0.4, H - 0.4), prio=1)

    # ---- GND stitching vias in free space
    nvia = 0
    yv = 2.0
    while yv < H - 1.5:
        xv = 2.0
        while xv < W - 1.5:
            vb = (xv - 0.6, yv - 0.6, xv + 0.6, yv + 0.6)
            inside_rf_line = 62.0 < xv < W and 8.0 < yv < 22.0
            if pl.free(vb) and not inside_rf_line:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(P(xv, yv))
                v.SetWidth(MM(0.6))
                v.SetDrill(MM(0.3))
                v.SetNet(gnd)
                board.Add(v)
                nvia += 1
            xv += 3.0
        yv += 3.0

    # ---- silkscreen
    add_text(board, "BRC-M400", 14.0, 4.2, 1.6, bold=True)
    add_text(board, "Rev C  -  INSATTECH", 15.5, 6.5, 0.9)
    labels = [
        ("E-PORT IN 24V", 6.8, 25.0, 0.85, 0),
        ("SWD", 27.5, 8.7, 0.85, 0), ("DJI PSDK", 44.0, 6.9, 0.85, 0), ("SWITCH", 66.0, 6.9, 0.85, 0),
        ("LoRa 868 MHz", 88.5, 21.8, 0.85, 0),
        ("LED ARRAY", 37.5, 49.4, 0.85, 0), ("HOLD MAG", 53.5, 49.4, 0.85, 0),
        ("EJECT SOL", 69.5, 49.4, 0.85, 0), ("SIREN", 88.5, 45.5, 0.85, 0),
    ]
    for txt, x, y, sz, rot in labels:
        t = add_text(board, txt, x, y, sz)
        t.SetTextAngleDegrees(rot)
    # back side branding
    add_text(board, "INSATTECH", W / 2, 9, 3.6, layer=pcbnew.B_SilkS, mirror=True, bold=True)
    add_text(board, "BRC-M400  Rev C", W / 2, 15, 2.8, layer=pcbnew.B_SilkS, mirror=True, bold=True)
    add_text(board, "Buoy Release & Beacon Controller", W / 2, 21, 1.6, layer=pcbnew.B_SilkS, mirror=True)
    add_text(board, "DJI Matrice 400  -  E-Port V2 / PSDK V3", W / 2, 25.5, 1.25, layer=pcbnew.B_SilkS, mirror=True)
    add_text(board, "STM32U585  +  Semtech SX1262  LoRa 868 MHz", W / 2, 29.2, 1.25, layer=pcbnew.B_SilkS, mirror=True)
    add_text(board, "Fail-safe hold magnet  +  ejection solenoid  +  ARM/FIRE interlock", W / 2, 33, 1.15,
             layer=pcbnew.B_SilkS, mirror=True)
    add_text(board, "AeroDay V14  -  Challenge CAO  -  2026", W / 2, 39, 1.4, layer=pcbnew.B_SilkS, mirror=True)


    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    pcbnew.SaveBoard(PCB, board)
    patch_stackup(PCB)
    write_project_rules()
    print("Board %gx%g mm, %d footprints, %d nets, %d stitching vias -> %s" % (
        W, H, len(fps), len(netobj), nvia, PCB))


if __name__ == "__main__":
    main()
