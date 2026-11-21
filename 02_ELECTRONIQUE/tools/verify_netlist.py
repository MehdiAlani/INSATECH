"""
Compare the netlist KiCad actually extracts from the schematic against the
intended netlist in gen_schematic.SHEETS. Catches any stub/label that failed
to connect. Usage:
    kicad-cli sch export netlist --format kicadsexpr -o out.net BRC-M400.kicad_sch
    python verify_netlist.py out.net
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sexp import load, head  # noqa: E402
import gen_schematic as G  # noqa: E402


def actual_groups(path):
    root = load(path)
    nets = None
    for ch in root:
        if head(ch) == 'nets':
            nets = ch
    groups = {}
    for net in nets[1:]:
        name = None
        nodes = set()
        for sub in net:
            h = head(sub)
            if h == 'name':
                name = sub[1][1]
            elif h == 'node':
                ref = pin = None
                for t in sub:
                    if head(t) == 'ref':
                        ref = t[1][1]
                    elif head(t) == 'pin':
                        pin = t[1][1]
                if ref and not ref.startswith('#'):
                    nodes.add((ref, pin))
        if nodes:
            groups[name] = frozenset(nodes)
    return groups


def expected_groups():
    groups = {}
    nc = set()
    for _, _, _, parts in G.SHEETS:
        for p in parts:
            if p.ref.startswith('#'):
                continue
            for pin, net in p.pins.items():
                if net is None:
                    nc.add((p.ref, pin))
                else:
                    groups.setdefault(net, set()).add((p.ref, pin))
    return {k: frozenset(v) for k, v in groups.items()}, nc


def main():
    act = actual_groups(sys.argv[1])
    exp, nc = expected_groups()
    act_sets = {v: k for k, v in act.items()}
    errors = 0
    for net, members in sorted(exp.items()):
        if members in act_sets:
            continue
        errors += 1
        # find where members ended up
        homes = {}
        for m in members:
            for an, am in act.items():
                if m in am:
                    homes.setdefault(an, []).append(m)
        print("MISMATCH %-14s expected %d pins; found split/merged as: %s" % (
            net, len(members), {k: sorted(v) for k, v in homes.items()}))
    # NC pins must be alone
    for an, am in act.items():
        bad = am & nc
        if bad and len(am) > 1:
            errors += 1
            print("NC pin connected:", an, sorted(am))
    print("Expected nets: %d | KiCad nets with parts: %d | mismatches: %d" % (
        len(exp), len(act), errors))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
