# -*- coding: utf-8 -*-
"""Rev D: the board now runs from a 3S LiPo (9.0 - 12.6 V) instead of the 24 V E-Port.

Coils are rewound for 12 V at the SAME power, so R is divided by 4 and L with it:
the L/R time constant - and therefore the mechanical timing - is preserved.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "sim_electronique.py")
s = io.open(p, encoding="utf-8").read()


def sub(a, b, n=1):
    global s
    assert s.count(a) >= n, "NOT FOUND: " + a[:80]
    s = s.replace(a, b, n)


# ------------------------------------------------------------------ gate drive rail
sub('Vdd vdd 0 11.85', 'Vdd vdd 0 11.96', 1)
sub('VDD = +12V_GD (11.85 V)', 'VDD = +12V_GD (11.96 V, elevateur TPS61040)')
sub('Vdd vdd 0 11.85', 'Vdd vdd 0 11.96')   # second occurrence inside COIL_STAGE replace()

# ------------------------------------------------------------------ 1. buck
sub('# 1. Logic-rail buck: LMR51430, 24 V -> 3.315 V, peak-current-mode, 500 kHz',
    '# 1. Logic-rail buck: LMR51430, 12.6 V pack -> 3.315 V, peak-current-mode, 500 kHz')
sub('Vin vin 0 24', 'Vin vin 0 12.6')
sub('print("\\n[1] Buck 24 V -> 3.3 V (rail logique)")',
    'print("\\n[1] Buck 12,6 V (pack 3S) -> 3,3 V (rail logique)")')

# ------------------------------------------------------------------ 2. system / input interruption
sub('* E-Port V2 VCC 24 V; input SHORTED to 0 V between 60 and 90 ms (fault test)',
    '* 3S pack 11.1 V; input INTERRUPTED between 60 and 90 ms (connector bounce / BMS trip)')
sub('Vsrc src 0 PWL(0 24 59.99m 24 60m 0 90m 0 90.01m 24 140m 24)',
    'Vsrc src 0 PWL(0 11.1 59.99m 11.1 60m 0 90m 0 90.01m 11.1 140m 11.1)')
sub('* --- LED array on VIN (24 V constant-voltage array: 20 V knee + 2 ohm), 1 kHz strobe',
    '* --- LED array on VIN (12 V array: 9 V knee + 0.8 ohm), 1 kHz strobe')

# ------------------------------------------------------------------ 3. LED stage
sub('# 3. LED array PWM stage: UCC27511A + BSC028N06LS3, 24 V / 2 A, 20 kHz',
    '# 3. LED array PWM stage: UCC27511A + BSC028N06LS3, 12 V / 3.75 A, 20 kHz')
sub('Vvin vin 0 24', 'Vvin vin 0 12')
sub('tf = edge(t, vds, 0.1 * 24, 0.9 * 24, 55e-6, 57e-6, False)',
    'tf = edge(t, vds, 0.1 * 12, 0.9 * 12, 55e-6, 57e-6, False)')
sub('tr = edge(t, vds, 0.1 * 24, 0.9 * 24, 80e-6, 82e-6, True)',
    'tr = edge(t, vds, 0.1 * 12, 0.9 * 12, 80e-6, 82e-6, True)')
sub('axs[0].set_title("LED array 24 V / %.1f A, PWM 20 kHz 50 %% - pertes MOSFET %.0f mW, Tj estimee %.0f C"',
    'axs[0].set_title("LED array 12 V / %.1f A, PWM 20 kHz 50 %% - pertes MOSFET %.0f mW, Tj estimee %.0f C"')

# ------------------------------------------------------------------ 4. siren
sub('Vvin vin 0 24', 'Vvin vin 0 12')      # siren stage

# ------------------------------------------------------------------ 5/6. coil stage + actuators
sub('COIL_STAGE = r"""Vact vact 0 PWL(0 0 0.5m 24)', 'COIL_STAGE = r"""Vact vact 0 PWL(0 0 0.5m 12)')
# ejection solenoid: 12 V / 4 ohm (same 36 W), L and dL/dx divided by 4 -> identical force and timing
sub('* Ejection solenoid 24 V / 16 ohm, stroke 10 mm, plunger+rod 30 g - BRC-M400 Rev C',
    '* Ejection solenoid 12 V / 4 ohm (36 W), stroke 10 mm, plunger+rod 30 g - BRC-M400 Rev D')
sub('Bemf 0 lam I = v(vact) - v(dn) - 16*v(ic)', 'Bemf 0 lam I = v(vact) - v(dn) - 4*v(ic)')
sub('Bic ic 0 V = v(lam) / (0.010 + 6e-4/(0.013 - v(x)))', 'Bic ic 0 V = v(lam) / (0.0025 + 1.5e-4/(0.013 - v(x)))')
sub('Bforce f 0 V = 0.5*v(ic)*v(ic)*6e-4/((0.013 - v(x))*(0.013 - v(x)))',
    'Bforce f 0 V = 0.5*v(ic)*v(ic)*1.5e-4/((0.013 - v(x))*(0.013 - v(x)))')
sub('axs[0].set_title("Solenoide d\'ejection 24 V - courant, course du plongeur et tension de drain")',
    'axs[0].set_title("Solenoide d\'ejection 12 V - courant, course du plongeur et tension de drain")')
# fail-safe holding magnet: 12 V / 14.4 ohm (10 W), L scaled with R -> same L/R
sub('* Fail-safe holding electromagnet 24 V / 57 ohm (10 W), L = 150 mH - BRC-M400 Rev C',
    '* Fail-safe holding electromagnet 12 V / 14.4 ohm (10 W), L = 37.9 mH - BRC-M400 Rev D')
sub('Lh vact hl 150m', 'Lh vact hl 37.9m')
sub('Rh hl dn 57', 'Rh hl dn 14.4')
sub('inom = 24 / 57', 'inom = 12 / 14.4')

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("sim_electronique.py -> Rev D (12 V)")
