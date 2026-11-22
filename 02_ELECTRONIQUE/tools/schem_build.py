"""Wired, compact block builder for gen_schematic.py.

layout_section() places + routes one functional block (in grid cells, origin free);
emit_section() writes its KiCad items at a given cell offset, so the blocks can either
go one per sheet (hierarchical) or side by side on a single page (flat).
"""
import math

import schem_layout as SL


class _Sym:
    flat_symbol = None
    head = None


def layout_section(M, sh, global_nets):
    _Sym.flat_symbol = staticmethod(M.flat_symbol)
    _Sym.head = staticmethod(M.head)
    parts = sh.parts
    label_pins = set()
    for net in sorted({nn for p in parts for nn in p.pins.values() if nn}):
        if net in global_nets and net not in SL.POWER_NETS:
            cands = [(len(p.pins), p.ref, num) for p in parts for num, nn in p.pins.items() if nn == net]
            cands.sort(key=lambda c: (-c[0], c[1], c[2]))
            label_pins.add((cands[0][1], cands[0][2]))

    best = None
    for margin in (1, 2, 3, 4, 5):
        placed = SL.place_sheet(_Sym, parts, label_pins, margin)
        paths, fails, _R = SL.route_sheet(placed, label_pins)
        if best is None or len(fails) < len(best[2]):
            best = (placed, paths, fails, margin)
        if not fails:
            break
    placed, paths, fails, margin = best
    sh.route_report = (margin, fails)
    sh.layout = (placed, paths, fails, label_pins)

    allc = [c for pl in placed for c in pl.keepout | set(pl.ends.values())]
    for plist in paths.values():
        for pth in plist:
            allc += pth
    sh.cbox = (min(c[0] for c in allc), min(c[1] for c in allc),
               max(c[0] for c in allc), max(c[1] for c in allc))
    sh.cw = sh.cbox[2] - sh.cbox[0] + 1      # size in grid cells
    sh.ch = sh.cbox[3] - sh.cbox[1] + 1


def emit_section(M, sh, ox, oy, counters, inst_path):
    """Emit the block with its top-left cell at grid cell (ox, oy). Returns KiCad items."""
    q, n, uid, duid, effects, label_angle = M.q, M.n, M.uid, M.duid, M.effects, M.label_angle
    GRID = M.GRID
    placed, paths, fails, label_pins = sh.layout
    offx, offy = ox - sh.cbox[0], oy - sh.cbox[1]

    def power_angle(net, dx, dy):
        if net in SL.GROUND_NETS:
            return {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[(dx, dy)]
        return {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(dx, dy)]

    def mm(c):
        return ((c[0] + offx) * GRID, (c[1] + offy) * GRID)

    def label_txt(net, X, Y, dx, dy):
        ang = label_angle(dx, dy)
        j = ("left" if ang in (0, 90) else "right") + " bottom"
        return '(label %s (at %s %s %d) (fields_autoplaced yes) %s (uuid %s))' % (
            q(net), n(X), n(Y), ang, effects(1.27, j), q(uid()))

    out = []
    pin_cells = {}
    for pl in placed:
        p = pl.p
        sh.lib_ids.add(p.lib_id)
        ox_mm = (pl.origin_cell[0] + offx) * GRID + pl.shift[0]
        oy_mm = (pl.origin_cell[1] + offy) * GRID + pl.shift[1]
        is_flag = p.lib_id == "power:PWR_FLAG"
        fpos = {name: (x, y, j) for name, x, y, j in pl.fields}
        fields = [("Reference", p.ref, not is_flag), ("Value", p.value, not is_flag), ("Footprint", p.fp, False),
                  ("Datasheet", M.symbol_prop_value(p.lib_id, "Datasheet"), False),
                  ("Description", M.symbol_prop_value(p.lib_id, "Description"), False)]
        if p.mpn:
            fields.append(("MPN", p.mpn, False))
        props_txt = []
        for (name, val, visible) in fields:
            fx, fy, j = fpos.get(name, (0.0, 0.0, None))
            fang = 90 if pl.th in (90, 270) else 0   # KiCad field angle is relative to the symbol
            props_txt.append('(property %s %s (at %s %s %d) %s)' % (
                q(name), q(val), n(ox_mm + fx), n(oy_mm + fy), fang, effects(1.27, j, not visible)))
        pins_txt = ' '.join('(pin %s (uuid %s))' % (q(num), q(uid())) for num in pl.pins)
        out.append(
            '(symbol (lib_id %s) (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom %s) '
            '(on_board %s) (dnp %s) (uuid %s) %s %s (instances (project %s (path %s '
            '(reference %s) (unit 1)))))' % (
                q(p.lib_id), n(ox_mm), n(oy_mm), pl.th,
                "no" if is_flag or p.lib_id.startswith("Mechanical:") else "yes",
                "no" if is_flag else "yes", "yes" if p.dnp else "no", q(duid("sym:" + p.ref)),
                ' '.join(props_txt), pins_txt, q(M.PROJECT), q(inst_path), q(p.ref)))

        for num, c in pl.ends.items():
            X, Y = mm(c)
            net = p.pins.get(num)
            dx, dy = pl.pins[num][2]
            if net is None:
                out.append('(no_connect (at %s %s) (uuid %s))' % (n(X), n(Y), q(uid())))
                continue
            pin_cells.setdefault(net, set()).add(c)
            if net in SL.POWER_NETS:
                lid = SL.POWER_NETS[net]
                sh.lib_ids.add(lid)
                counters['pwr'] += 1
                ref = "#PWR%03d" % counters['pwr']
                ang = power_angle(net, dx, dy)
                vx, vy = X + dx * 4.6, Y + dy * 4.6
                vj = "left" if dx > 0 else ("right" if dx < 0 else None)
                out.append(
                    '(symbol (lib_id %s) (at %s %s %d) (unit 1) (exclude_from_sim no) '
                    '(in_bom yes) (on_board yes) (dnp no) (uuid %s) '
                    '(property "Reference" %s (at %s %s 0) %s) '
                    '(property "Value" %s (at %s %s 0) %s) '
                    '(property "Footprint" "" (at %s %s 0) %s) '
                    '(property "Datasheet" "" (at %s %s 0) %s) '
                    '(property "Description" "" (at %s %s 0) %s) '
                    '(pin "1" (uuid %s)) (instances (project %s (path %s (reference %s) (unit 1)))))' % (
                        q(lid), n(X), n(Y), ang, q(duid("pwr:" + ref)),
                        q(ref), n(X), n(Y), effects(1.27, None, True),
                        q(net), n(vx), n(vy), effects(1.0, vj),
                        n(X), n(Y), effects(1.27, None, True),
                        n(X), n(Y), effects(1.27, None, True),
                        n(X), n(Y), effects(1.27, None, True),
                        q(uid()), q(M.PROJECT), q(inst_path), q(ref)))
            elif (p.ref, num) in label_pins:
                X, Y = mm((c[0] + 2 * dx, c[1] + 2 * dy))     # end of the 2-cell wire stub
                ang = label_angle(dx, dy)
                just = "left" if ang in (0, 90) else "right"
                out.append(
                    '(global_label %s (shape passive) (at %s %s %d) (fields_autoplaced yes) %s (uuid %s) '
                    '(property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) %s))' % (
                        q(net), n(X), n(Y), ang, effects(1.27, just), q(uid()),
                        n(X), n(Y), effects(1.27, just, True)))

    seginfo = SL.path_segments(paths)
    for net, (segs, nodes) in seginfo.items():
        for a, b in segs:
            (x1, y1), (x2, y2) = mm(a), mm(b)
            out.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))' % (
                n(x1), n(y1), n(x2), n(y2), q(uid())))
    for c in SL.junctions(seginfo, pin_cells):
        X, Y = mm(c)
        out.append('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid %s))' % (n(X), n(Y), q(uid())))

    # fallback (should stay empty): local label on unreachable pins + one on the routed tree
    failed_keys = {(f[0], f[1]) for f in fails}
    tree_labelled = set()
    bypart = {pl.p.ref: pl for pl in placed}
    for ref, num, net in fails:
        pl = bypart[ref]
        X, Y = mm(pl.ends[num])
        dx, dy = pl.pins[num][2]
        out.append(label_txt(net, X, Y, dx, dy))
        if net in tree_labelled:
            continue
        tree_labelled.add(net)
        for pl2 in placed:
            hit = [k for k, nn in pl2.p.pins.items() if nn == net and (pl2.p.ref, k) not in failed_keys]
            if hit:
                X, Y = mm(pl2.ends[hit[0]])
                dx, dy = pl2.pins[hit[0]][2]
                out.append(label_txt(net, X, Y, dx, dy))
                break
    return out


def build_sheet_wired(M, sh, global_nets, counters):
    """Hierarchical mode: one block per sheet, title + notes at the top."""
    q, n, uid, effects = M.q, M.n, M.uid, M.effects
    GRID = M.GRID
    layout_section(M, sh, global_nets)
    top = 25.0 + 6.0 * len(sh.notes) + 6.0
    w_mm, h_mm = (sh.cw - 1) * GRID + 10, (sh.ch - 1) * GRID + 10
    paper = "A1"
    for pp, (W, H) in (("A4", (297, 210)), ("A3", (420, 297)), ("A2", (594, 420)), ("A1", (841, 594))):
        if w_mm + 30 <= W and h_mm + top + 45 <= H:
            paper = pp
            break
    sh.paper = paper
    out = ['(text %s (exclude_from_sim no) (at 15 14 0) %s (uuid %s))' % (
        q(sh.title.upper()), effects(3.0, "left bottom"), q(uid()))]
    for i, line in enumerate(sh.notes):
        out.append('(text %s (exclude_from_sim no) (at 15 %s 0) %s (uuid %s))' % (
            q(line), n(21 + 6 * i), effects(1.8, "left bottom"), q(uid())))
    out += emit_section(M, sh, int(math.ceil(20.0 / GRID)), int(math.ceil(top / GRID)), counters, sh.path)
    sh.items = out
