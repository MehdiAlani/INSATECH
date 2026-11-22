"""
Compact placement + orthogonal wire routing for generated KiCad schematic sheets.

Conventions kept from hand-drawn schematics:
  * power nets (GND and supply rails) -> power symbols on each pin
  * nets shared with other sheets     -> ONE global label per sheet, wired to every pin
  * every other net                   -> real wires (no labels)

Routing happens on a 2.54 mm grid and obeys KiCad's connection semantics so nets
can never merge by accident:
  * a cell holding a pin end / wire end / bend / junction of net A is taboo for any other net
  * two nets never share a collinear segment
  * perpendicular crossings are allowed only where both wires pass straight through
"""
import heapq
import math

G = 2.54
POWER_NETS = {"GND": "power:GND", "VIN": "power:VCC", "+3V3": "power:+3V3",
              "+3V3_RF": "power:VDD", "+12V_GD": "power:+12V",
              "BATT_N": "power:GNDPWR", "PACK_P": "power:VBUS"}
GROUND_NETS = {"GND", "BATT_N"}          # symbols that point DOWN
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BEND, CROSS, STEP = 3, 2, 1


def cell(v):
    return int(round(v / G))


def rot(x, y, th):
    """Rotate a screen-relative point (Y down) by th degrees CCW (as KiCad displays)."""
    t = math.radians(th)
    c, s = round(math.cos(t), 9), round(math.sin(t), 9)
    return x * c + y * s, -x * s + y * c


def outward_vec(angle):
    a = math.radians(angle + 180.0)
    return int(round(math.cos(a))), -int(round(math.sin(a)))


# ---------------------------------------------------------------------------
# Symbol geometry
# ---------------------------------------------------------------------------
def symbol_geometry(S, lib_id):
    """Pins [(num, x, y, angle, length)] and body bbox, library coords converted to screen (Y down)."""
    node = S.flat_symbol(lib_id)
    pins, pts = [], []

    def walk(n):
        for ch in n:
            if not isinstance(ch, list):
                continue
            h = S.head(ch)
            if h == 'pin':
                at = num = None
                length = 2.54
                for sub in ch:
                    hh = S.head(sub)
                    if hh == 'at':
                        at = [float(t[1]) for t in sub[1:]]
                    elif hh == 'number':
                        num = sub[1][1]
                    elif hh == 'length':
                        length = float(sub[1][1])
                pins.append((num, at[0], -at[1], at[2] if len(at) > 2 else 0.0, length))
            elif h in ('rectangle', 'polyline', 'circle', 'arc', 'bezier'):
                for sub in ch:
                    hh = S.head(sub)
                    if hh in ('start', 'end', 'mid', 'center'):
                        pts.append((float(sub[1][1]), -float(sub[2][1])))
                    elif hh == 'pts':
                        for xy in sub[1:]:
                            pts.append((float(xy[1][1]), -float(xy[2][1])))
                    elif hh == 'radius' and h == 'circle':
                        r = float(sub[1][1])
                        if pts:
                            cx, cy = pts[-1]
                            pts.extend([(cx - r, cy - r), (cx + r, cy + r)])
            elif h == 'symbol':
                walk(ch)
    walk(node)
    if not pts:   # power symbols etc.: roots of pins
        pts = [(0.0, 0.0)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return pins, (min(xs), min(ys), max(xs), max(ys))


class Placed:
    """One part with a chosen rotation; geometry relative to its origin."""

    def __init__(self, S, part, th, power_nets, label_pins):
        self.p, self.th = part, th
        pins, (bx0, by0, bx1, by1) = symbol_geometry(S, part.lib_id)
        corners = [rot(x, y, th) for x, y in ((bx0, by0), (bx1, by1), (bx0, by1), (bx1, by0))]
        self.body = (min(c[0] for c in corners), min(c[1] for c in corners),
                     max(c[0] for c in corners), max(c[1] for c in corners))
        self.pins = {}
        for num, x, y, a, length in pins:
            rx, ry = rot(x, y, th)
            self.pins[num] = (rx, ry, outward_vec(a + th), length)
        # parity: put pin ends on the 2.54 grid
        fx = fy = 0.0
        if self.pins:
            x0, y0 = next(iter(self.pins.values()))[:2]
            fx = G / 2 if round(x0 / (G / 2)) % 2 else 0.0
            fy = G / 2 if round(y0 / (G / 2)) % 2 else 0.0
        self.shift = (fx, fy)
        self.power_nets, self.label_pins = power_nets, label_pins
        self.origin = None

    def pin_cells_rel(self):
        out = {}
        for num, (x, y, v, L) in self.pins.items():
            out[num] = (cell(x + self.shift[0]), cell(y + self.shift[1]))
        return out

    def keepout_rel(self, field_boxes):
        """Cells this part occupies (body, pin lines, power symbols, labels, text), relative."""
        sx, sy = self.shift
        cells = set()
        x0, y0, x1, y1 = self.body
        for i in range(cell(x0 + sx), cell(x1 + sx) + 1):
            for j in range(cell(y0 + sy), cell(y1 + sy) + 1):
                cells.add((i, j))
        ends = self.pin_cells_rel()
        for num, (x, y, (dx, dy), L) in self.pins.items():
            ex, ey = ends[num]
            k = max(1, int(round(L / G)))
            for t in range(1, k + 1):
                cells.add((ex - dx * t, ey - dy * t))
            net = self.p.pins.get(num)
            if net in self.power_nets:
                # the symbol sits on the pin's own line; neighbours' exits stay free
                for t in (1, 2):
                    cells.add((ex + dx * t, ey + dy * t))
            elif net is not None and (self.p.ref, num) in self.label_pins:
                n = 2 + int(len(net) * 1.0 / G) + 1
                for t in range(3, n + 3):          # t = 1..2 is the wire stub to the label
                    cells.add((ex + dx * t, ey + dy * t))
        for (fx0, fy0, fx1, fy1) in field_boxes:
            for i in range(cell(fx0 + sx), cell(fx1 + sx) + 1):
                for j in range(cell(fy0 + sy), cell(fy1 + sy) + 1):
                    cells.add((i, j))
        return cells - set(ends.values())


# ---------------------------------------------------------------------------
# Field (Reference / Value) placement
# ---------------------------------------------------------------------------
def field_layout(S, pl):
    """[(name, x_rel, y_rel, justify)] and their text boxes (relative, mm)."""
    p = pl.p
    n_pins = len(pl.pins)
    ref, val = p.ref, p.value
    tw = lambda s: 1.05 * len(s) + 0.6
    vertical = n_pins == 2 and all(v[2][1] != 0 for v in pl.pins.values())
    if vertical:
        # vertical 2-pin part: text to the right
        x = pl.body[2] + 0.9
        f = [("Reference", x, -0.9, "left"), ("Value", x, 1.6, "left")]
        boxes = [(x, -1.9, x + tw(ref), -0.1), (x, 0.6, x + tw(val), 2.4)]
        return f, boxes
    if n_pins == 2:
        y0, y1 = pl.body[1] - 1.6, pl.body[3] + 1.6
        f = [("Reference", 0.0, y0, None), ("Value", 0.0, y1, None)]
        boxes = [(-tw(ref) / 2, y0 - 1.0, tw(ref) / 2, y0 + 0.8), (-tw(val) / 2, y1 - 0.8, tw(val) / 2, y1 + 1.0)]
        return f, boxes
    # multi-pin: reference above the body, value below it (both left-aligned on the body)
    x = pl.body[0]
    ya, yb = pl.body[1] - 1.6, pl.body[3] + 1.8
    f = [("Reference", x, ya, "left"), ("Value", x, yb, "left")]
    boxes = [(x, ya - 1.0, x + tw(ref), ya + 0.8), (x, yb - 0.8, x + tw(val), yb + 1.0)]
    return f, boxes


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------
def dilate(cells, m):
    out = set()
    for (i, j) in cells:
        for di in range(-m, m + 1):
            for dj in range(-m, m + 1):
                out.add((i + di, j + dj))
    return out


def candidate_rotations(part, pins_geom_nets):
    n = len(part.pins)
    if n != 2:
        return [0]
    nets = list(part.pins.values())
    return [0, 90, 180, 270]


def rotation_ok(pl):
    """Power-tied 2-pin parts: supply pin up, GND pin down."""
    if len(pl.pins) != 2:
        return True
    for num, (x, y, (dx, dy), L) in pl.pins.items():
        net = pl.p.pins.get(num)
        if net == "GND" and dy != 1:
            return False
        if net in POWER_NETS and net not in GROUND_NETS and dy != -1:
            return False
    return True


def place_sheet(S, parts, label_pins, margin):
    placed = []
    used = set()
    net_pins = {}          # net -> list of absolute pin cells (placed)
    net_out = {}           # net -> list of (cell, outward) of placed pins, in placement order

    def local_nets(p):
        return [n for n in p.pins.values() if n and n not in POWER_NETS]

    unplaced = list(parts)
    # seed: the part with the most pins
    unplaced.sort(key=lambda p: -len(p.pins))

    def score(p):
        shared = sum(1 for n in set(local_nets(p)) if n in net_pins)
        pw = sum(1 for n in set(p.pins.values()) if n in POWER_NETS and n != "GND" and n in net_pins)
        return (shared, pw * 0.1, len(p.pins))

    first = True
    while unplaced:
        if first:
            p = unplaced[0]
        else:
            p = max(unplaced, key=score)
        unplaced.remove(p)
        best = None
        rots = candidate_rotations(p, None)
        okrots = [th for th in rots if rotation_ok(Placed(S, p, th, POWER_NETS, label_pins))]
        if not okrots:            # e.g. a ferrite between two rails: any orientation
            okrots = [r for r in rots if r in (90, 270)] or rots
        for th in okrots:
            pl = Placed(S, p, th, POWER_NETS, label_pins)
            fields, boxes = field_layout(S, pl)
            ko = pl.keepout_rel(boxes)
            ends = pl.pin_cells_rel()
            rel_all = ko | set(ends.values())
            footprint = dilate(rel_all, margin)
            # desired origin
            tgt = []
            facing = 0.0
            for num, net in p.pins.items():
                if net and net in net_out and (net not in POWER_NETS or (net != "GND" and not local_nets(p))):
                    # sit just off the pin it connects to (first placed pin of that net = usually the IC)
                    (ac, (adx, ady)) = net_out[net][0]
                    gap = margin + 2
                    want = (ac[0] + adx * gap, ac[1] + ady * gap)
                    ex, ey = ends[num]
                    tgt.append((want[0] - ex, want[1] - ey))
                    # our pin should point back toward the anchor
                    odx, ody = pl.pins[num][2]
                    if odx * adx + ody * ady >= 0 and (adx or ady):
                        facing += 4.0
            if first or not tgt:
                if placed:
                    allx = [c[0] for c in used]
                    ally = [c[1] for c in used]
                    ox, oy = max(allx) + margin + 4, (min(ally) + max(ally)) // 2
                else:
                    ox, oy = 0, 0
            else:
                ox = int(round(sum(t[0] for t in tgt) / len(tgt)))
                oy = int(round(sum(t[1] for t in tgt) / len(tgt)))
            # spiral search
            found = None
            for r in range(0, 120):
                ring = []
                if r == 0:
                    ring = [(0, 0)]
                else:
                    for k in range(-r, r + 1):
                        ring += [(k, -r), (k, r), (-r, k), (r, k)]
                ring.sort(key=lambda d: abs(d[0]) + abs(d[1]))
                for dx, dy in ring:
                    cx, cy = ox + dx, oy + dy
                    if all((i + cx, j + cy) not in used for (i, j) in footprint):
                        found = (cx, cy)
                        break
                if found:
                    break
            cost = 0.0
            for num, net in p.pins.items():
                if net and net in net_pins and net not in POWER_NETS:
                    cs = net_pins[net]
                    ex, ey = ends[num]
                    cost += min(abs(found[0] + ex - c[0]) + abs(found[1] + ey - c[1]) for c in cs)
            cost += 0.3 * (abs(found[0] - ox) + abs(found[1] - oy)) + facing
            if best is None or cost < best[0]:
                best = (cost, pl, found, fields, ko, ends)
        cost, pl, (cx, cy), fields, ko, ends = best
        pl.origin_cell = (cx, cy)
        pl.fields = fields
        pl.keepout = {(i + cx, j + cy) for (i, j) in ko}
        pl.ends = {num: (i + cx, j + cy) for num, (i, j) in ends.items()}
        used |= pl.keepout | set(pl.ends.values())
        for num, net in p.pins.items():
            if net:
                net_pins.setdefault(net, []).append(pl.ends[num])
                net_out.setdefault(net, []).append((pl.ends[num], pl.pins[num][2]))
        placed.append(pl)
        first = False
    return placed


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
class Router:
    def __init__(self, blocked):
        self.blocked = set(blocked)       # cells nobody may enter
        self.node = {}                    # cell -> net  (pin end, wire end, bend, junction)
        self.seg = {}                     # cell -> {net: set('h','v')}

    def legal_enter(self, c, net, d):
        if c in self.blocked:
            return False
        o = self.node.get(c)
        if o is not None and o != net:
            return False
        s = self.seg.get(c)
        if s:
            for other, axes in s.items():
                if other == net:
                    return False                    # do not run over own wire (start states cover that)
                if ('h' if d[1] == 0 else 'v') in axes:
                    return False                    # collinear overlap
        return True

    def is_cross(self, c, net):
        s = self.seg.get(c)
        return bool(s) and any(o != net for o in s)

    def route(self, net, starts, target, targets_own, bbox):
        """A* from any start cell to target. Returns list of cells."""
        x0, y0, x1, y1 = bbox
        tx, ty = target
        pq = []
        best = {}
        for sc in starts:
            st = (sc, None)
            best[st] = 0
            heapq.heappush(pq, (abs(sc[0] - tx) + abs(sc[1] - ty), 0, sc, None, None))
        parent = {}
        while pq:
            f, g, c, d, prev = heapq.heappop(pq)
            if best.get((c, d), 1e18) < g:
                continue
            if c == target:
                path = [c]
                key = (c, d)
                while key in parent:
                    key = parent[key]
                    path.append(key[0])
                return path[::-1]
            crossing_here = self.is_cross(c, net)
            for nd in DIRS:
                if crossing_here and d is not None and nd != d:
                    continue
                if d is not None and nd == (-d[0], -d[1]):
                    continue
                n2 = (c[0] + nd[0], c[1] + nd[1])
                if not (x0 <= n2[0] <= x1 and y0 <= n2[1] <= y1):
                    continue
                if n2 != target and n2 in targets_own:
                    continue
                if n2 != target and not self.legal_enter(n2, net, nd):
                    continue
                if n2 == target:
                    o = self.node.get(n2)
                    if o is not None and o != net:
                        continue
                    if self.is_cross(n2, net):
                        continue
                    if n2 in self.blocked:
                        continue
                cost = g + STEP + (BEND if (d is not None and nd != d) else 0) \
                    + (CROSS if self.is_cross(n2, net) else 0)
                # can't end or turn on a crossing: a crossing cell must be passed straight
                key = (n2, nd)
                if cost < best.get(key, 1e18):
                    best[key] = cost
                    parent[key] = (c, d)
                    h = abs(n2[0] - tx) + abs(n2[1] - ty)
                    heapq.heappush(pq, (cost + h, cost, n2, nd, None))
        return None

    def commit(self, net, path):
        for k, c in enumerate(path):
            prev = path[k - 1] if k > 0 else None
            nxt = path[k + 1] if k + 1 < len(path) else None
            axes = set()
            if prev:
                axes.add('h' if prev[1] == c[1] else 'v')
            if nxt:
                axes.add('h' if nxt[1] == c[1] else 'v')
            self.seg.setdefault(c, {}).setdefault(net, set()).update(axes)
            is_node = (k == 0 or k == len(path) - 1 or len(axes) > 1)
            if is_node:
                self.node[c] = net


def route_sheet(placed, label_pins):
    """Returns ({net: [paths]}, failures[(ref, pin, net)])."""
    blocked = set()
    terminals = {}
    for pl in placed:
        blocked |= pl.keepout
        for num, c in pl.ends.items():
            net = pl.p.pins.get(num)
            if net is None or net in POWER_NETS:
                blocked.add(c)
                continue
            terminals.setdefault(net, []).append((c, pl.p.ref, num))
    R = Router(blocked)
    for net, ts in terminals.items():
        for (c, ref, num) in ts:
            R.node[c] = net
    allc = [c for pl in placed for c in pl.keepout | set(pl.ends.values())]
    gx0, gx1 = min(c[0] for c in allc) - 6, max(c[0] for c in allc) + 6
    gy0, gy1 = min(c[1] for c in allc) - 6, max(c[1] for c in allc) + 6

    # short nets first
    def span(ts):
        xs = [t[0][0] for t in ts]
        ys = [t[0][1] for t in ts]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))
    paths, fails = {}, []
    stubs = {}
    for pl in placed:
        for num, c in pl.ends.items():
            if (pl.p.ref, num) in label_pins:
                net = pl.p.pins[num]
                dx, dy = pl.pins[num][2]
                stub = [c, (c[0] + dx, c[1] + dy), (c[0] + 2 * dx, c[1] + 2 * dy)]
                R.commit(net, stub)
                stubs[net] = stub
                paths[net] = [stub]
    order = sorted((n for n in terminals if len(terminals[n]) > 1), key=lambda n: span(terminals[n]))
    for net in order:
        ts = terminals[net]
        uniq = []
        for t in ts:
            if t[0] not in [u[0] for u in uniq]:
                uniq.append(t)
        if len(uniq) < 2:
            continue
        if net in stubs:
            tree = set(stubs[net])
            todo = [u for u in uniq if u[0] not in tree]
        else:
            tree = {uniq[0][0]}
            todo = uniq[1:]
            paths[net] = []
        while todo:
            # nearest remaining terminal to the tree
            todo.sort(key=lambda t: min(abs(t[0][0] - c[0]) + abs(t[0][1] - c[1]) for c in tree))
            t = todo.pop(0)
            if t[0] in tree:
                continue
            starts = [c for c in tree if not R.is_cross(c, net)]
            others = {u[0] for u in todo}
            xs = [c[0] for c in tree] + [t[0][0]]
            ys = [c[1] for c in tree] + [t[0][1]]
            got = None
            for pad in (8, 20, 60):
                bb = (max(gx0, min(xs) - pad), max(gy0, min(ys) - pad), min(gx1, max(xs) + pad), min(gy1, max(ys) + pad))
                got = R.route(net, starts, t[0], others, bb)
                if got:
                    break
            if not got:
                fails.append((t[1], t[2], net))
                continue
            R.commit(net, got)
            paths[net].append(got)
            tree |= set(got)
    return paths, fails, R


def path_segments(paths):
    """Per net: list of ((x1,y1),(x2,y2)) cell segments, split at every node of that net."""
    out = {}
    for net, plist in paths.items():
        nodes = set()
        runs = []
        for p in plist:
            nodes.add(p[0])
            nodes.add(p[-1])
            for k in range(1, len(p) - 1):
                a, b, c = p[k - 1], p[k], p[k + 1]
                if (a[0] == b[0]) != (b[0] == c[0]):
                    nodes.add(b)
            runs.append(p)
        segs = []
        for p in runs:
            start = p[0]
            for k in range(1, len(p)):
                c = p[k]
                last = (k == len(p) - 1)
                nxt = p[k + 1] if not last else None
                turn = nxt is not None and ((p[k - 1][0] == c[0]) != (c[0] == nxt[0]))
                if last or turn or c in nodes:
                    if c != start:
                        segs.append((start, c))
                    start = c
        out[net] = (segs, nodes)
    return out


def junctions(seginfo, pin_cells):
    """Cells where >= 3 wire ends/pins meet on a net -> junction dots."""
    res = []
    for net, (segs, nodes) in seginfo.items():
        cnt = {}
        for a, b in segs:
            cnt[a] = cnt.get(a, 0) + 1
            cnt[b] = cnt.get(b, 0) + 1
        for c, k in cnt.items():
            if k + (1 if c in pin_cells.get(net, set()) else 0) >= 3:
                res.append(c)
    return res
