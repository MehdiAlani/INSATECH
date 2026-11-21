"""
Generates SIM_LED_PWM.kicad_sch: a self-contained KiCad simulation of the
BRC-M400 LED-array power stage (open it, Inspect > Simulator > Run).

Reuses the schematic engine of 02_ELECTRONIQUE/tools/gen_schematic.py
(real library symbols, no hand-typed pins).
"""
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "02_ELECTRONIQUE", "tools"))
sys.path.insert(0, TOOLS)
import gen_schematic as G  # noqa: E402

NAME = "SIM_LED_PWM"
FET = ("vto=1.7 kp=180 rd=0.9m rs=0.4m rg=1 lambda=0.01 cgs=4.2n cgdmax=2n cgdmin=40p "
       "a=0.3 cjo=1.6n is=2e-11 rb=2m bv=66")

# ref, lib_id, value, (x, y), {pin: net}, extra fields
PARTS = [
    ("V1", "Simulation_SPICE:VDC", "24V E-Port", (40, 70), {1: "VIN", 2: "GND"},
     {"Sim.Device": "V", "Sim.Type": "DC", "Sim.Pins": "1=+ 2=-", "Sim.Params": "dc=24"}),
    ("V2", "Simulation_SPICE:VPULSE", "PWM 20kHz 50%", (70, 120), {1: "DRV", 2: "GND"},
     {"Sim.Device": "V", "Sim.Type": "PULSE", "Sim.Pins": "1=+ 2=-",
      "Sim.Params": "y1=0 y2=12 td=5u tr=5n tf=5n tw=25u per=50u"}),
    ("R1", "Device:R", "4.7", (95, 112), {1: "DRV", 2: "GATE"}, {}),
    ("R2", "Device:R", "10k", (115, 128), {1: "GATE", 2: "GND"}, {}),
    ("Q1", "Simulation_SPICE:NMOS", "BSC028N06LS3", (135, 112), {1: "DRAIN", 2: "GATE", 3: "SRC"},
     {"Sim.Device": "NMOS", "Sim.Type": "VDMOS", "Sim.Pins": "1=D 2=G 3=S", "Sim.Params": FET}),
    ("R3", "Device:R", "10m", (135, 135), {1: "SRC", 2: "GND"}, {}),
    ("L1", "Device:L", "1u", (135, 40), {1: "VIN", 2: "LA"}, {}),
    ("R4", "Device:R", "2", (135, 55), {1: "LA", 2: "LB"}, {}),
    ("D2", "Simulation_SPICE:D", "LED string", (135, 70), {1: "LC", 2: "LB"},
     {"Sim.Device": "D", "Sim.Pins": "1=K 2=A", "Sim.Params": "is=1e-12 n=0.3"}),
    ("V3", "Simulation_SPICE:VDC", "Vf 20V", (135, 87), {1: "LC", 2: "DRAIN"},
     {"Sim.Device": "V", "Sim.Type": "DC", "Sim.Pins": "1=+ 2=-", "Sim.Params": "dc=20"}),
    ("D1", "Simulation_SPICE:D", "SS54", (170, 70), {1: "VIN", 2: "DRAIN"},
     {"Sim.Device": "D", "Sim.Pins": "1=K 2=A", "Sim.Params": "is=5e-5 n=1.1 rs=0.02 cjo=400p bv=40"}),
    ("#FLG01", "power:PWR_FLAG", "PWR_FLAG", (40, 95), {1: "GND"}, {}),
]

NOTES = [
    ("SIMULATION - ETAGE LED ARRAY PWM (BRC-M400)", 3.0),
    ("1. Inspect > Simulator   2. Run (fleche verte)   3. Add Signals : V(/DRAIN), V(/GATE), I(L1)", 2.0),
    ("4. Supprimez D1 (ou passez-le en 'Exclude from simulation') et relancez : surtension > 60 V au blocage", 2.0),
    ("V3 + D2 + R4 = LED array 24 V (seuil 20 V, 2 ohm) ; L1 = cablage 1 uH ; R3 = shunt 10 mOhm", 1.6),
]
DIRECTIVE = ".tran 1n 105u"


def build():
    items, lib_ids = [], set()
    pwr = [0]
    for ref, lib_id, value, (ox, oy), pins, extra in PARTS:
        ox, oy = G.snap(ox), G.snap(oy)   # connection points on the 1.27 mm grid
        lib_ids.add(lib_id)
        pinmap = {num: (x, -y, a) for num, x, y, a in G.symbol_pins(lib_id)}
        lprops = G.symbol_props(lib_id)
        fields = [("Reference", ref, True), ("Value", value, True), ("Footprint", "", False),
                  ("Datasheet", "", False), ("Description", "", False)]
        fields += [(k, v, False) for k, v in extra.items()]
        ptxt = []
        for name, val, vis in fields:
            lx, ly, la, _ = lprops.get(name, (0.0, 0.0, 0.0, True))
            ptxt.append('(property %s %s (at %s %s %s) %s)' % (
                G.q(name), G.q(val), G.n(ox + lx), G.n(oy - ly), G.n(la), G.effects(1.27, None, not vis)))
        pins_txt = ' '.join('(pin %s (uuid %s))' % (G.q(k), G.q(G.uid())) for k in pinmap)
        items.append('(symbol (lib_id %s) (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) '
                     '(dnp no) (uuid %s) %s %s (instances (project %s (path %s (reference %s) (unit 1)))))' % (
                         G.q(lib_id), G.n(ox), G.n(oy), G.q(G.uid()), ' '.join(ptxt), pins_txt,
                         G.q(NAME), G.q("/" + ROOT), G.q(ref)))
        for num, (px, py, a) in pinmap.items():
            net = pins[int(num)]
            X, Y = ox + px, oy + py
            dx, dy = G.outward(a)
            EX, EY = X + dx * 2.54, Y + dy * 2.54
            items.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))' % (
                G.n(X), G.n(Y), G.n(EX), G.n(EY), G.q(G.uid())))
            if net == "GND":
                pwr[0] += 1
                r = "#PWR%02d" % pwr[0]
                lib_ids.add("power:GND")
                items.append(
                    '(symbol (lib_id "power:GND") (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom yes) '
                    '(on_board yes) (dnp no) (uuid %s) (property "Reference" %s (at %s %s 0) %s) '
                    '(property "Value" "GND" (at %s %s 0) %s) (property "Footprint" "" (at %s %s 0) %s) '
                    '(property "Datasheet" "" (at %s %s 0) %s) (property "Description" "" (at %s %s 0) %s) '
                    '(pin "1" (uuid %s)) (instances (project %s (path %s (reference %s) (unit 1)))))' % (
                        G.n(EX), G.n(EY), G.q(G.uid()), G.q(r), G.n(EX), G.n(EY + 6), G.effects(1.27, None, True),
                        G.n(EX), G.n(EY + 3.8), G.effects(1.27), G.n(EX), G.n(EY), G.effects(1.27, None, True),
                        G.n(EX), G.n(EY), G.effects(1.27, None, True), G.n(EX), G.n(EY), G.effects(1.27, None, True),
                        G.q(G.uid()), G.q(NAME), G.q("/" + ROOT), G.q(r)))
            else:
                ang = G.label_angle(dx, dy)
                just = "left" if ang in (0, 90) else "right"
                items.append('(label %s (at %s %s %d) (fields_autoplaced yes) %s (uuid %s))' % (
                    G.q(net), G.n(EX), G.n(EY), ang, G.effects(1.27, just + " bottom"), G.q(G.uid())))
    y = 160
    for txt, size in NOTES:
        items.append('(text %s (exclude_from_sim no) (at 30 %s 0) %s (uuid %s))' % (
            G.q(txt), G.n(y), G.effects(size, "left bottom"), G.q(G.uid())))
        y += 7
    # the analysis directive (a schematic text item that the simulator reads)
    items.append('(text %s (exclude_from_sim no) (at 30 25 0) %s (uuid %s))' % (
        G.q(DIRECTIVE), G.effects(2.0, "left bottom"), G.q(G.uid())))
    body = ['(kicad_sch (version 20250610) (generator "eeschema") (generator_version "10.0")',
            '(uuid %s)' % G.q(ROOT), '(paper "A4")',
            '(title_block (title "BRC-M400 - Simulation etage LED PWM") (date "2026-11-21") (rev "B"))',
            G.lib_symbols_block(lib_ids)] + items + ['(sheet_instances (path "/" (page "1")))',
                                                      '(embedded_fonts no)', ')']
    with open(os.path.join(HERE, NAME + ".kicad_sch"), "w", encoding="utf-8", newline="\n") as f:
        f.write('\n'.join(body) + '\n')
    pro = os.path.join(HERE, NAME + ".kicad_pro")
    if not os.path.exists(pro):
        with open(pro, "w") as f:
            f.write('{\n  "meta": {\n    "filename": "%s.kicad_pro",\n    "version": 3\n  }\n}\n' % NAME)
    print("written", NAME + ".kicad_sch")


ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, "brc-m400/sim-led"))

if __name__ == "__main__":
    build()
