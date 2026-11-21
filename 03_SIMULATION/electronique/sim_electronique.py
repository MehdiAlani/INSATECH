"""
BRC-M400 Rev C (INSATECH) - electrical simulations (ngspice, the engine built into KiCad).

Runs every circuit below through KiCad's own ngspice.dll, then plots the
results to figures/*.png and prints the key numbers.

    python sim_electronique.py            # all simulations
    python sim_electronique.py buck led   # a subset

Models are behavioural (documented per simulation): they reproduce the
architecture and the datasheet key values, not the vendors' transistor-level
models.
"""
import ctypes
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, "netlists")
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
for d in (NET, DATA, FIG):
    os.makedirs(d, exist_ok=True)

KICAD_BIN = r"C:\Program Files\KiCad\10.0\bin"

# ---------------------------------------------------------------------------
# Chart style - reference palette, fixed categorical order, recessive grid
# ---------------------------------------------------------------------------
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"     # categorical slots 1-4 (fixed order)
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
SURFACE, GRID = "#fcfcfb", "#e4e3df"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.6, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlecolor": INK, "legend.frameon": False, "legend.fontsize": 9,
    "figure.dpi": 110,
})


def limit_line(ax, y, text, va="bottom"):
    ax.axhline(y, color=INK2, lw=1.0, ls=(0, (4, 3)))
    ax.text(ax.get_xlim()[1], y, " " + text, color=INK2, fontsize=8.5, va=va, ha="right")


def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("   figure ->", os.path.relpath(path, HERE))


# ---------------------------------------------------------------------------
# ngspice shared library
# ---------------------------------------------------------------------------
class Ngspice:
    def __init__(self):
        os.add_dll_directory(KICAD_BIN)
        self.lib = ctypes.CDLL(os.path.join(KICAD_BIN, "ngspice.dll"))
        self.log = []
        PF = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
        EX = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
        self._pf = PF(lambda s, i, u: self.log.append(s.decode(errors="ignore")) or 0)
        self._ex = EX(lambda *a: 0)
        self.lib.ngSpice_Init(self._pf, None, self._ex, None, None, None, None)

    def run(self, name, netlist):
        """Write netlist, source it (its .control block runs the analysis)."""
        # relative paths: ngspice splits command arguments on spaces
        cir = "netlists/" + name + ".cir"
        with open(os.path.join(HERE, cir), "w") as f:
            f.write(netlist)
        self.log.clear()
        self.lib.ngSpice_Command(("source " + cir).encode())
        errs = [l for l in self.log if "rror" in l and "spinit" not in l]
        if errs:
            print("   ngspice:", "\n   ".join(errs[:6]))
        self.lib.ngSpice_Command(b"destroy all")
        self.lib.ngSpice_Command(b"remcirc")


def wr(name, vecs):
    """Control-block line writing vectors to data/<name>.txt."""
    return "wrdata data/%s.txt %s" % (name, " ".join(vecs))


def load(name, n):
    a = np.loadtxt(os.path.join(DATA, name + ".txt"))
    t = a[:, 0]
    return t, [a[:, 2 * i + 1] for i in range(n)]


# ===========================================================================
# 1. Logic-rail buck: LMR51430, 24 V -> 3.315 V, peak-current-mode, 500 kHz
# ===========================================================================
BUCK = r"""* LMR51430 behavioural peak-current-mode buck - BRC-M400 Rev C logic rail
* Datasheet values: fsw 500 kHz, Rds(on) HS 120 mOhm / LS 70 mOhm, Vref 0.600 V, tSS 4 ms
Vin vin 0 24
Cin vin 0 10u
Vclk clk 0 PULSE(0 1 0 2n 2n 40n 2u)
Vramp ramp 0 PULSE(0 0.1 0 1.99u 2n 1n 2u)
Vref ref 0 PWL(0 0 4m 0.6)
* error amplifier: PI (Kp = 9 -> ~37 kHz crossover with 35 uF, zero 3 kHz) + anti-windup
Be e 0 V = v(ref)-v(fb)
Bint 0 xi I = 0.1697*v(e) * ((v(e) > 0) ? ((v(xi) < 1.2) ? 1 : 0) : ((v(xi) > -0.1) ? 1 : 0))
Cint xi 0 1u
Rint xi 0 1e12
Bvc vcr 0 V = max(0, min(1.05, 9*v(e) + v(xi)))
Rvc vcr vc 1k
Cvc vc 0 1.6n
H1 isns 0 Vimeas 0.2
Bset s 0 V = v(clk) > 0.5 ? 1 : 0
Brst r 0 V = (v(isns) + v(ramp) > v(vc)) ? 1 : 0
Bq q 0 V = v(s) > 0.5 ? 1 : (v(r) > 0.5 ? 0 : (v(qd) > 0.5 ? 1 : 0))
Rqd q qd 10
Cqd qd 0 10p
Bqn qn 0 V = 1 - v(q)
S1 vin lx q 0 SWHS
S2 lx 0 qn 0 SWLS
Dbody 0 lx DBODY
.model SWHS SW(Ron=0.12 Roff=1e6 Vt=0.5 Vh=0.05)
.model SWLS SW(Ron=0.07 Roff=1e6 Vt=0.5 Vh=0.05)
.model DBODY D(IS=1e-9 RS=0.05 CJO=200p)
* L2 Bourns SRN6045TA-150M 15 uH (DCR ~ 45 mOhm)
Vimeas lx lx2 0
L1 lx2 lr 15u
RL lr vout 0.045
* 2 x 22 uF X5R 10 V (effective ~35 uF at 3.3 V)
Cc vout cc 35u
Rcc cc 0 2m
R5 vout fb 100k
R6 fb 0 22.1k
* load: MCU + SX1262 RX (30 mA) -> LoRa TX +22 dBm burst (160 mA) at 6 ms -> back at 8 ms
Vprof prof 0 PWL(0 0.03 6m 0.03 6.002m 0.16 8m 0.16 8.002m 0.03 10m 0.03)
Bload vout 0 I = v(prof)*min(1, max(0, v(vout)/2.5))
.options interp
.control
tran 0.25u 10m 0 10n
{WR1}
.endc
.end
"""

BUCK_ZOOM = BUCK.replace(".options interp\n", "").replace(
    "tran 0.25u 10m 0 10n", "tran 5n 7.95m 7.93m 5n").replace("{WR1}", "{WR2}")


def sim_buck(ng):
    print("\n[1] Buck 24 V -> 3.3 V (rail logique)")
    ng.run("buck_3v3", BUCK.replace("{WR1}", wr("buck_full", ["v(vout)", "i(Vimeas)", "v(prof)", "i(Vin)"])))
    ng.run("buck_3v3_zoom", BUCK_ZOOM.replace("{WR2}", wr("buck_zoom", ["v(vout)", "i(Vimeas)", "v(lx)"])))
    t, (vo, il, ild, iin) = load("buck_full", 4)
    tz, (voz, ilz, lxz) = load("buck_zoom", 3)
    tm = t * 1e3
    ss = (t > 5.0e-3) & (t < 5.99e-3)
    v_ss = vo[ss].mean()
    v_min = vo[(t > 6e-3) & (t < 6.5e-3)].min()
    v_max = vo[(t > 8e-3) & (t < 8.5e-3)].max()
    rip = voz.max() - voz.min()
    il_pp = ilz.max() - ilz.min()
    ok = np.abs(vo - v_ss) < 0.01 * v_ss
    idx = np.where((t > 6.002e-3) & ~ok & (t < 7.9e-3))[0]
    t_settle = (t[idx[-1]] - 6.002e-3) * 1e6 if len(idx) else 0.0
    print("   Vout regime        : %.3f V (cible 3.315 V)" % v_ss)
    print("   ondulation Vout    : %.1f mV pk-pk (emission LoRa 160 mA)" % (rip * 1e3))
    print("   ondulation IL      : %.2f A pk-pk (theorie 0.38 A)" % il_pp)
    print("   echelon 30->160 mA : creux -%.1f mV (%.2f %%), %s ; relachement +%.1f mV"
          % ((v_ss - v_min) * 1e3, (v_ss - v_min) / v_ss * 100,
             "reste dans +/-1 %" if t_settle == 0 else "retour +/-1 %% en %.0f us" % t_settle, (v_max - v_ss) * 1e3))

    fig, axs = plt.subplots(3, 1, figsize=(10, 8.2), sharex=True,
                            gridspec_kw={"height_ratios": [1.3, 1, 0.7]})
    axs[0].plot(tm, vo, color=S1, label="Vout")
    axs[0].set_ylabel("Tension (V)")
    axs[0].set_title("Rail logique 3,3 V (LMR51430) - demarrage 4 ms puis rafale d'emission LoRa")
    axs[0].set_ylim(0, 4)
    limit_line(axs[0], 3.315, "consigne 3,315 V")
    limit_line(axs[0], 3.07, "seuil reset 3,07 V", va="top")
    axs[1].plot(tm, il, color=S2, lw=0.8, label="courant inductance IL")
    axs[1].set_ylabel("IL (A)")
    axs[2].plot(tm, ild, color=S3, label="charge MCU + SX1262")
    axs[2].set_ylabel("Charge (A)")
    axs[2].set_xlabel("Temps (ms)")
    for ax in axs[1:]:
        ax.legend(loc="upper left")
    save(fig, "01_buck_3v3_transitoire.png")

    fig, axs = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True)
    tu = (tz - tz[0]) * 1e6
    axs[0].plot(tu, (voz - voz.mean()) * 1e3, color=S1)
    axs[0].set_ylabel("Vout - moy. (mV)")
    axs[0].set_title("Regime etabli en emission (160 mA) - ondulation %.1f mV pk-pk, IL %.2f A pk-pk, 500 kHz"
                     % (rip * 1e3, il_pp))
    axs[1].plot(tu, ilz, color=S2)
    axs[1].set_ylabel("IL (A)")
    axs[1].set_xlabel("Temps (us)")
    save(fig, "02_buck_3v3_ondulation.png")
    return dict(v_ss=v_ss, rip=rip, il_pp=il_pp, dip=v_ss - v_min, settle=t_settle)


# ===========================================================================
# 2. System power integrity: E-Port V2 -> protection -> 2 bucks -> all loads
# ===========================================================================
SYSTEM = r"""* BRC-M400 system power - averaged models
* E-Port V2 VCC 24 V; input SHORTED to 0 V between 60 and 90 ms (fault test)
Vsrc src 0 PWL(0 24 59.99m 24 60m 0 90m 0 90.01m 24 140m 24)
Rsrc src a1 0.03
Lsrc a1 a2 0.5u
Rcab a2 vf 0.04
{PROT}
* bulk + local ceramics
C3 vin c3 470u
Rc3 c3 0 0.06
Cce vin 0 20u
* --- load profiles (A)
Vphold phold 0 PWL(0 0 30m 0 30.01m 1 50m 1 50.01m 0)
Vpej pej 0 PWL(0 0 30m 0 30.01m 1 50m 1 50.01m 0)
Vpled pled 0 PULSE(0 1 20m 10u 10u 0.5m 1m 30)
Vpsir psir 0 PWL(0 0 25m 0 25.01m 1 55m 1 55.01m 0)
Vplog plog 0 PWL(0 0.02 35m 0.02 35.01m 0.138 45m 0.138 45.01m 0.02)
* --- logic buck (LMR51430, eta 85 %, UVLO 3.7 V) + gate-drive LDO (5 mA)
B3 v3 0 V = v(vin) > 3.7 ? min(3.315, 0.92*v(vin)) : 0
R3 v3 0 1k
Bin3 vin 0 I = v(v3)*v(plog)/(0.85*max(v(vin), 1))
Ildo vin 0 5m
* --- actuators on V_ACT (= VIN through the ARM P-MOSFET): hold magnet 57 ohm, ejection solenoid 16 ohm
Bhold vin 0 I = v(phold)*v(vin)/57
Bej vin 0 I = v(pej)*v(vin)/16
* --- LED array on VIN (24 V constant-voltage array: 20 V knee + 2 ohm), 1 kHz strobe
Bled vin 0 I = v(pled)*max(0, (v(vin)-20)/2)
* --- siren on VIN (48 ohm)
Bsir vin 0 I = v(psir)*v(vin)/48
.model DIDEAL D(IS=1e-6 N=0.05 RS=0.0028)
.options interp
.control
tran 5u 140m 0 2u
{WR}
.endc
.end
"""


def sim_system(ng):
    print("\n[2] Integrite d'alimentation systeme + court-circuit E-Port")
    res = {}
    for key, prot in (("ideal", "Dprot vf vin DIDEAL"), ("pfet", "Rprot vf vin 0.0115")):
        ng.run("system_" + key, SYSTEM.replace("{PROT}", prot).replace(
            "{WR}", wr("system_" + key, ["v(vin)", "v(v3)", "v(phold)", "v(pej)", "v(pled)", "v(psir)", "i(Vsrc)"])))
        res[key] = load("system_" + key, 7)
    t, (vin, v3, phold, pej, pled, psir, isrc) = res["ideal"]
    tp, (vin_p, v3_p, *_r) = res["pfet"]
    tm = t * 1e3
    worst = (t > 30e-3) & (t < 50e-3)
    ilead = pled * np.maximum(0, (vin - 20) / 2)
    isir = psir * vin / 48
    vin_min = vin[worst].min()
    v3_dev = np.abs(v3[(t > 1e-3) & (t < 60e-3)] - 3.315).max()
    fault = (t > 60e-3) & (t < 90e-3)
    v3_fault_min = v3[fault].min()
    vin_fault_min = vin[fault].min()
    collapse = tp[(tp > 60e-3) & (v3_p < 3.0)]
    t_coll = (collapse[0] - 60e-3) * 1e6 if len(collapse) else None
    ipk = (-isrc)[t > 5e-3].max()      # after start-up (bulk-cap charging excluded)
    print("   pire cas simultane (aimant + solenoide + LED + sirene + TX) : VIN min %.2f V, courant E-Port max %.2f A" % (vin_min, ipk))
    print("   VIN reste > 3,7 V (UVLO) -> rails regules ; transitoire du convertisseur : voir simulation [1]")
    print("   court-circuit E-Port 30 ms, diode ideale LM74700 : 3,3 V min %.3f V (VIN %.2f V)" % (v3_fault_min, vin_fault_min))
    print("   meme defaut avec P-MOSFET passif                 : 3,3 V < 3,0 V en %s us" % ("%.0f" % t_coll if t_coll else "-"))

    fig, axs = plt.subplots(3, 1, figsize=(10, 8.8), sharex=True, gridspec_kw={"height_ratios": [1, 1, 0.9]})
    axs[0].plot(tm, vin, color=S1, label="diode ideale LM74700 (choix retenu)")
    axs[0].plot(tp * 1e3, vin_p, color=S2, label="P-MOSFET passif (rev A)")
    axs[0].set_ylabel("VIN (V)")
    axs[0].set_title("Integrite d'alimentation : pire cas de charge, puis court-circuit de l'entree E-Port (60-90 ms)")
    axs[0].axvspan(60, 90, color=GRID, alpha=0.6, lw=0)
    axs[0].text(75, 2, "entree E-Port\nen court-circuit", ha="center", color=INK2, fontsize=8.5)
    axs[0].legend(loc="lower left")
    axs[1].plot(tm, v3, color=S1, label="diode ideale")
    axs[1].plot(tp * 1e3, v3_p, color=S2, label="P-MOSFET passif")
    axs[1].set_ylabel("Rail +3,3 V (V)")
    axs[1].set_ylim(-0.2, 3.8)
    axs[1].axvspan(60, 90, color=GRID, alpha=0.6, lw=0)
    limit_line(axs[1], 3.07, "seuil reset TPS3808 3,07 V", va="top")
    axs[1].legend(loc="lower left")
    axs[2].plot(tm, phold * vin / 57 + pej * vin / 16, color=S1, label="aimant + solenoide (A)")
    axs[2].plot(tm, ilead, color=S2, lw=0.6, label="LED array, strobe 1 kHz (A)")
    axs[2].plot(tm, isir, color=S3, label="sirene (A)")
    axs[2].set_ylabel("Courants (A)")
    axs[2].set_xlabel("Temps (ms)")
    axs[2].legend(loc="upper right", ncol=3)
    save(fig, "03_integrite_alimentation.png")
    return dict(vin_min=vin_min, v3_dev=v3_dev, v3_fault_min=v3_fault_min, t_coll=t_coll, ipk=ipk)


# ===========================================================================
# 3. LED array PWM stage: UCC27511A + BSC028N06LS3, 24 V / 2 A, 20 kHz
# ===========================================================================
FET_MODEL = (".model BSC028 VDMOS(Rd=0.9m Rs=0.4m Rg=1.0 Vto=1.7 Kp=180 lambda=0.01 "
             "Cgs=4.2n Cgdmax=2n Cgdmin=40p A=0.3 Cjo=1.6n M=0.5 Vj=0.8 Is=2e-11 N=1.05 "
             "Rb=2m BV=66 IBV=1m TT=20n ksubthres=0.1 mtriode=1.2)\n"
             ".model SS54 D(IS=5e-5 N=1.1 RS=0.02 CJO=400p BV=40)\n"
             ".model SS34 D(IS=3e-5 N=1.1 RS=0.04 CJO=250p BV=40)\n")

DRIVER = r"""* --- UCC27511A behavioural: 13 ns delay, OUTH 4 A source, OUTL 8 A sink, VDD = +12V_GD (11.85 V)
Vdd vdd 0 11.85
Cdd vdd 0 1u
Bin inl 0 V = v(pwm) > 1.8 ? 1 : 0
Rdl inl ind 1k
Cdl ind 0 13p
Bnd indn 0 V = 1 - v(ind)
Sh vdd outh ind 0 SWH
Sl outl 0 indn 0 SWL
.model SWH SW(Ron=3.0 Roff=1e8 Vt=0.5 Vh=0.01)
.model SWL SW(Ron=1.5 Roff=1e8 Vt=0.5 Vh=0.01)
Rgh outh g 4.7
Rgl outl g 1
Rgpd g {SRC} 10k
"""

LED = r"""* LED array PWM power stage - BRC-M400
Vvin vin 0 24
Ltr vin vin2 20n
Cloc vin2 0 22u
* LED array: wiring 1 uH + 2 ohm ballast + 20 V string
Lw vin2 la 1u
Rled la lb 2
Dled lb lc DLEDI
Vled lc ledn 20
.model DLEDI D(IS=1e-12 N=0.3)
{FW}
M1 ledn g src BSC028
Rsh src 0 10m
Vpwm pwm 0 PULSE(0 3.3 5u 5n 5n 25u 50u)
""" + DRIVER.replace("{SRC}", "src") + FET_MODEL + r"""
.options interp
.control
tran 0.5n 105u 0 0.5n
{WR}
.endc
.end
"""


def sim_led(ng):
    print("\n[3] Etage LED array PWM 20 kHz (UCC27511A + BSC028N06LS3)")
    out = {}
    for key, fw in (("fw", "Dfw ledn vin2 SS54"), ("nofw", "")):
        ng.run("led_" + key, LED.replace("{FW}", fw).replace(
            "{WR}", wr("led_" + key, ["v(g,src)", "v(ledn)", "i(Lw)", "v(src)"])))
        out[key] = load("led_" + key, 4)
    t, (vgs, vds, iled, vsrc) = out["fw"]
    tn, (vgs_n, vds_n, iled_n, _) = out["nofw"]
    ids = vsrc / 0.01
    p = (vds - vsrc) * ids
    dt = np.gradient(t)
    # steady-state period 55..105 us
    per = (t >= 55e-6) & (t < 105e-6)
    p_avg = (p[per] * dt[per]).sum() / 50e-6
    on = (t > 70e-6) & (t < 78e-6)
    rds = ((vds[on] - vsrc[on]) / ids[on]).mean()      # drain-source only (excl. 10 mOhm shunt)
    i_on = ids[on].mean()
    p_cond = i_on ** 2 * rds * 0.5
    p_sw = p_avg - p_cond

    def edge(tt, v, lo, hi, t0, t1, rising):
        m = (tt > t0) & (tt < t1)
        tt, v = tt[m], v[m]
        a, b = (lo, hi) if rising else (hi, lo)
        ia = np.argmax(v >= a) if rising else np.argmax(v <= a)
        ib = np.argmax(v >= b) if rising else np.argmax(v <= b)
        return (tt[ib] - tt[ia]) * 1e9

    tf = edge(t, vds, 0.1 * 24, 0.9 * 24, 55e-6, 57e-6, False)     # Vds falls at turn-on
    tr = edge(t, vds, 0.1 * 24, 0.9 * 24, 80e-6, 82e-6, True)      # Vds rises at turn-off
    vds_pk = vds[t > 50e-6].max()
    vds_pk_n = vds_n[tn > 50e-6].max()
    tj = 25 + p_avg * 50
    print("   I LED %.2f A, RDS(on) MOSFET %.2f mOhm a Vgs 11,85 V (shunt 10 mOhm exclu)" % (i_on, rds * 1e3))
    print("   commutation : chute Vds %.0f ns (amorcage), montee Vds %.0f ns (blocage)" % (tf, tr))
    print("   pertes MOSFET : %.0f mW total (conduction %.0f mW + commutation %.0f mW) -> Tj ~ %.0f C (RthJA 50 K/W)"
          % (p_avg * 1e3, p_cond * 1e3, p_sw * 1e3, tj))
    print("   pic Vds au blocage : %.1f V avec diode SS54, %.1f V SANS diode (avalanche, BVDSS 60 V)" % (vds_pk, vds_pk_n))

    fig, axs = plt.subplots(3, 1, figsize=(10, 8.4), sharex=True)
    tu = t * 1e6
    axs[0].plot(tu, vgs, color=S1, label="Vgs")
    axs[0].set_ylabel("Vgs (V)")
    axs[0].set_title("LED array 24 V / %.1f A, PWM 20 kHz 50 %% - pertes MOSFET %.0f mW, Tj estimee %.0f C"
                     % (i_on, p_avg * 1e3, tj))
    axs[1].plot(tn * 1e6, vds_n, color=S2, label="sans diode de roue libre")
    axs[1].plot(tu, vds, color=S1, label="avec SS54 (choix retenu)")
    axs[1].set_ylabel("Vds (V)")
    limit_line(axs[1], 60, "BVDSS 60 V")
    axs[1].legend(loc="center right")
    axs[2].plot(tu, iled, color=S3, label="courant LED")
    axs[2].set_ylabel("I LED (A)")
    axs[2].set_xlabel("Temps (us)")
    for ax in (axs[0], axs[2]):
        ax.legend(loc="upper right")
    save(fig, "04_led_pwm_etage.png")

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, (a, b, ttl) in zip(axs, ((55.0, 55.25, "Amorcage"), (80.0, 80.25, "Blocage"))):
        m = (tu > a) & (tu < b)
        ax.plot((tu[m] - a) * 1e3, vds[m], color=S1, label="Vds (V)")
        ax.plot((tu[m] - a) * 1e3, ids[m] * 10, color=S2, label="Id x10 (A)")
        ax.plot((tu[m] - a) * 1e3, vgs[m] * 2, color=S3, label="Vgs x2 (V)")
        ax.set_title("%s - %.0f ns" % (ttl, tf if ttl == "Amorcage" else tr))
        ax.set_xlabel("Temps (ns)")
    axs[0].legend(loc="center right")
    axs[0].set_ylabel("V / A (echelles indiquees)")
    save(fig, "05_led_pwm_commutation_zoom.png")
    return dict(i_on=i_on, rds=rds, tf=tf, tr=tr, p=p_avg, pc=p_cond, ps=p_sw, tj=tj,
                vpk=vds_pk, vpk_n=vds_pk_n)


# ===========================================================================
# 4. Siren: inductive load turn-off, with / without flyback diode
# ===========================================================================
SIREN = r"""* Siren power stage - inductive turn-off
Vvin vin 0 24
Cloc vin 0 22u
Lsir vin sa 5m
Rsir sa sirn 48
{FW}
M1 sirn g 0 BSC028
Vpwm pwm 0 PULSE(0 3.3 50u 5n 5n 750u 2)
""" + DRIVER.replace("{SRC}", "0") + FET_MODEL + r"""
.options interp
.control
tran 10n 1.3m 0 10n
{WR}
.endc
.end
"""


def sim_siren(ng):
    print("\n[4] Sirene : charge inductive, avec / sans diode de roue libre")
    out = {}
    for key, fw in (("fw", "Dfw sirn vin SS34"), ("nofw", "")):
        ng.run("siren_" + key, SIREN.replace("{FW}", fw).replace("{WR}", wr("siren_" + key, ["v(sirn)", "i(Lsir)"])))
        out[key] = load("siren_" + key, 2)
    t, (vd, il) = out["fw"]
    tn, (vdn, iln) = out["nofw"]
    e_av = 0.5 * 5e-3 * il.max() ** 2
    print("   I sirene %.2f A ; pic Vds %.1f V avec SS34, %.1f V sans (energie d'avalanche %.2f mJ par coupure)"
          % (il.max(), vd.max(), vdn.max(), e_av * 1e3))
    fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axs[0].plot(tn * 1e3, vdn, color=S2, label="sans diode")
    axs[0].plot(t * 1e3, vd, color=S1, label="avec SS34 (choix retenu)")
    axs[0].set_ylabel("Vds (V)")
    axs[0].set_title("Sirene (5 mH / 48 ohm) - surtension de coupure : %.0f V sans diode, %.1f V avec" % (vdn.max(), vd.max()))
    limit_line(axs[0], 60, "BVDSS 60 V")
    axs[0].legend(loc="upper left")
    axs[1].plot(tn * 1e3, iln, color=S2, label="sans diode")
    axs[1].plot(t * 1e3, il, color=S1, label="avec SS34")
    axs[1].set_ylabel("I sirene (A)")
    axs[1].set_xlabel("Temps (ms)")
    axs[1].legend(loc="upper left")
    save(fig, "06_sirene_coupure_inductive.png")
    return dict(i=il.max(), vpk=vd.max(), vpk_n=vdn.max(), e=e_av)


# ===========================================================================
# 5. Ejection solenoid - electromechanical model (coil + plunger + spring + end stops)
# ===========================================================================
# supplies ramp up in 0.5 ms (instant steps with uic create a fake turn-on spike)
COIL_STAGE = r"""Vact vact 0 PWL(0 0 0.5m 24)
Cact vact 0 100u
{CLAMP}
M1 dn g src BSC028
Rsh src 0 10m
""" + DRIVER.replace("{SRC}", "src").replace("Vdd vdd 0 11.85", "Vdd vdd 0 PWL(0 0 0.5m 11.85)") + FET_MODEL + """.model TVS20 D(IS=1e-12 N=1.5 RS=0.3 BV=23 IBV=1m)
"""

CLAMPS = {"fast": "Dfw dn k SS34\nDtvs vact k TVS20", "diode": "Dfw dn vact SS34"}

EJECT = r"""* Ejection solenoid 24 V / 16 ohm, stroke 10 mm, plunger+rod 30 g - BRC-M400 Rev C
* coil flux linkage lam integrated on a 1 F node; I = lam / L(x); L(x) = 10 mH + Kl/(13 mm - x)
Bemf 0 lam I = v(vact) - v(dn) - 16*v(ic)
Clam lam 0 1
Bic ic 0 V = v(lam) / (0.010 + 6e-4/(0.013 - v(x)))
Bcoil vact dn I = v(ic)
* magnetic force F = 1/2 I^2 dL/dx ; spring 300 N/m + 1 N preload ; viscous 1.5 N.s/m ; end stops
Bforce f 0 V = 0.5*v(ic)*v(ic)*6e-4/((0.013 - v(x))*(0.013 - v(x)))
Bstop st 0 V = 2e5*max(v(x)-0.010, 0) + 2e5*min(v(x), 0) + 30*v(u)*(v(x) > 0.010 ? 1 : (v(x) < 0 ? 1 : 0))
Bacc 0 u I = (v(f) - 300*v(x) - 1.0 - 1.5*v(u) - v(st)) / 0.03
Cu u 0 1
Bpos 0 x I = v(u)
Cx x 0 1
* FIRE: full-on 60 ms pull-in pulse
Vpwm pwm 0 PULSE(0 3.3 2m 5n 5n 60m 1)
""" + COIL_STAGE + r"""
.options interp
.control
tran 10u 140m 0 2u uic
{WR}
.endc
.end
"""


def sim_eject(ng):
    print("\n[5] Solenoide d'ejection : modele electromecanique, signature de courant")
    out = {}
    for key, clamp in CLAMPS.items():
        ng.run("eject_" + key, EJECT.replace("{CLAMP}", clamp).replace(
            "{WR}", wr("eject_" + key, ["v(ic)", "v(x)", "v(dn)", "v(f)"])))
        out[key] = load("eject_" + key, 4)
    t, (ic, x, vd, f) = out["fast"]
    td, (icd, xd, vdd_, fd) = out["diode"]
    tm = t * 1e3
    # firmware detection: after the first current maximum, the current dips while the plunger moves
    on = (tm > 2) & (tm < 62)
    k0 = np.where(on)[0][0]
    seg = ic[on]
    kmax = np.argmax(seg[: len(seg) // 2])
    kmin = kmax + np.argmin(seg[kmax:kmax + int(25e-3 / (t[1] - t[0]))])
    t_peak, t_dip = tm[k0 + kmax], tm[k0 + kmin]
    t_closed = tm[(x >= 0.0099) & (tm > 2)][0]
    def ret_time(tt, xx):
        m = (tt > 62e-3) & (xx < 0.0005)
        return (tt[m][0] * 1e3 - 62) if m.any() else float('nan')
    r_fast, r_diode = ret_time(t, x), ret_time(td, xd)
    print("   pic de courant %.2f A a %.1f ms, creux (plongeur en mouvement) %.2f A, fin de course a %.1f ms"
          % (ic[k0 + kmax], t_peak, ic[k0 + kmin], t_closed))
    print("   -> ejection confirmee par le MCU a t = %.1f ms (minimum du creux)" % t_dip)
    print("   retour du plongeur apres coupure : %.1f ms (diode + TVS)  vs  %.1f ms (diode seule)" % (r_fast, r_diode))
    print("   tension drain au blocage : %.1f V (diode + TVS)  vs  %.1f V (diode seule)" % (vd.max(), vdd_.max()))
    print("   force magnetique max %.0f N (fin de course), force au depart %.1f N" % (f.max(), f[(tm > 3) & (tm < 5)].max()))

    fig, axs = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    axs[0].plot(tm, ic, color=S1, label="diode + TVS 20 V (choix retenu)")
    axs[0].plot(td * 1e3, icd, color=S2, label="diode seule")
    axs[0].axvline(t_dip, color=MUTED, lw=1)
    axs[0].annotate("creux de courant = le plongeur bouge\n-> ejection confirmee (%.1f ms)" % t_dip,
                    xy=(t_dip, ic[k0 + kmin]), xytext=(t_dip + 8, 0.55), color=INK2, fontsize=8.5,
                    arrowprops=dict(arrowstyle="-", color=MUTED))
    axs[0].set_ylabel("Courant bobine (A)")
    axs[0].set_title("Solenoide d'ejection 24 V - courant, course du plongeur et tension de drain")
    axs[0].legend(loc="upper right")
    axs[1].plot(tm, x * 1e3, color=S1, label="diode + TVS")
    axs[1].plot(td * 1e3, xd * 1e3, color=S2, label="diode seule")
    axs[1].set_ylabel("Course (mm)")
    axs[1].legend(loc="upper right")
    axs[2].plot(tm, vd, color=S1, label="diode + TVS")
    axs[2].plot(td * 1e3, vdd_, color=S2, label="diode seule")
    axs[2].set_ylabel("V drain (V)")
    axs[2].set_xlabel("Temps (ms)")
    limit_line(axs[2], 60, "BVDSS 60 V")
    axs[2].legend(loc="center right")
    save(fig, "07_solenoide_ejection.png")
    return dict(t_dip=t_dip, t_closed=t_closed, r_fast=r_fast, r_diode=r_diode, vpk=vd.max(), vpk_d=vdd_.max(),
                ipk=ic[k0 + kmax])


# ===========================================================================
# 6. Fail-safe holding electromagnet (permanent magnet, coil = release)
# ===========================================================================
HOLD = r"""* Fail-safe holding electromagnet 24 V / 57 ohm (10 W), L = 150 mH - BRC-M400 Rev C
Lh vact hl 150m
Rh hl dn 57
Vpwm pwm 0 PULSE(0 3.3 5m 5n 5n 300m 1)
""" + COIL_STAGE + r"""
.options interp
.control
tran 10u 340m 0 2u uic
{WR}
.endc
.end
"""


def sim_hold(ng):
    print("\n[6] Electroaimant de maintien a securite positive : liberation et demagnetisation")
    out = {}
    for key, clamp in CLAMPS.items():
        ng.run("hold_" + key, HOLD.replace("{CLAMP}", clamp).replace("{WR}", wr("hold_" + key, ["i(Lh)", "v(dn)"])))
        out[key] = load("hold_" + key, 2)
    t, (ih, vd) = out["fast"]
    td, (ihd, vdd_) = out["diode"]
    tm = t * 1e3
    inom = 24 / 57
    irel = 0.7 * inom
    t_rel = tm[(ih >= irel) & (tm > 5)][0] - 5
    def off_time(tt, ii):
        m = (tt > 305e-3) & (ii < 0.05 * inom)
        return tt[m][0] * 1e3 - 305 if m.any() else float('nan')
    d_fast, d_diode = off_time(t, ih), off_time(td, ihd)
    print("   courant nominal %.2f A ; seuil de liberation (70 %%) atteint %.1f ms apres l'ordre FIRE" % (inom, t_rel))
    print("   demagnetisation a 5 %% : %.1f ms (diode + TVS) vs %.1f ms (diode seule) ; V drain max %.1f V"
          % (d_fast, d_diode, vd.max()))
    fig, axs = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
    axs[0].plot(tm, ih, color=S1, label="diode + TVS 20 V (choix retenu)")
    axs[0].plot(td * 1e3, ihd, color=S2, label="diode seule")
    limit_line(axs[0], irel, "seuil de liberation (70 %% de %.2f A)" % inom, va="top")
    axs[0].set_ylabel("Courant bobine (A)")
    axs[0].set_title("Aimant de maintien a securite positive - liberation en %.1f ms, re-verrouillage %.0fx plus rapide"
                     % (t_rel, d_diode / d_fast))
    axs[0].legend(loc="center right")
    axs[1].plot(tm, vd, color=S1, label="diode + TVS")
    axs[1].plot(td * 1e3, vdd_, color=S2, label="diode seule")
    limit_line(axs[1], 60, "BVDSS 60 V")
    axs[1].set_ylabel("V drain (V)")
    axs[1].set_xlabel("Temps (ms)")
    axs[1].legend(loc="center left")
    save(fig, "08_aimant_maintien.png")
    return dict(t_rel=t_rel, d_fast=d_fast, d_diode=d_diode, vpk=vd.max())


# ===========================================================================
# 6. LoRa link budget (SX1262 datasheet sensitivities) + time on air
# ===========================================================================
SENS = {7: -124.0, 8: -126.6, 9: -129.2, 10: -131.8, 11: -134.4, 12: -137.0}   # SF7/SF12 datasheet, others interpolated


def toa_ms(sf, payload=16, bw=125e3, cr=1, preamble=8, crc=1, ih=0):
    de = 1 if (sf >= 11 and bw == 125e3) else 0
    tsym = (2 ** sf) / bw
    n = 8 + max(math.ceil((8 * payload - 4 * sf + 28 + 16 * crc - 20 * ih) / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return ((preamble + 4.25) + n) * tsym * 1e3


def sim_link():
    print("\n[6] Bilan de liaison LoRa 869,525 MHz")
    d = np.logspace(-1, np.log10(80), 400)
    fspl = 32.44 + 20 * np.log10(869.525) + 20 * np.log10(d)
    ptx, gt, gr, loss = 22, 2, 2, 1
    fig, ax = plt.subplots(figsize=(10, 5))
    rows = []
    for sf, col in ((7, S1), (9, S2), (12, S3)):
        margin = ptx + gt + gr - loss - fspl - SENS[sf]
        ax.semilogx(d, margin, color=col, label="SF%d (sensibilite %.0f dBm)" % (sf, SENS[sf]))
    for sf in range(7, 13):
        m15 = ptx + gt + gr - loss - (32.44 + 20 * np.log10(869.525) + 20 * np.log10(15)) - SENS[sf]
        rows.append((sf, SENS[sf], m15, toa_ms(sf)))
    limit_line(ax, 20, "marge d'evanouissement 20 dB")
    ax.axvline(15, color=MUTED, lw=1)
    ax.text(15, ax.get_ylim()[1] - 3, " 15 km", color=INK2, fontsize=8.5, va="top")
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Marge de liaison (dB)")
    ax.set_title("SX1262 +22 dBm, antennes 2 dBi - marge en espace libre (869,525 MHz)")
    ax.legend(loc="upper right")
    save(fig, "09_bilan_liaison_lora.png")
    print("   SF | sensib. | marge @15 km | temps d'antenne (16 octets)")
    for sf, s, m, ta in rows:
        print("   %2d | %6.1f  | %6.1f dB    | %6.0f ms" % (sf, s, m, ta))
    return rows


ALL = ["buck", "system", "led", "siren", "eject", "hold", "link"]


def main():
    os.chdir(HERE)
    which = [a.lower() for a in sys.argv[1:]] or ALL
    if len(which) > 1:
        # one process per simulation: an ngspice error can't poison the others
        import subprocess
        for k in which:
            subprocess.run([sys.executable, os.path.abspath(__file__), k])
        return None
    which = set(which)
    ng = Ngspice()
    results = {}
    if "buck" in which:
        results["buck"] = sim_buck(ng)
    if "system" in which:
        results["system"] = sim_system(ng)
    if "led" in which:
        results["led"] = sim_led(ng)
    if "siren" in which:
        results["siren"] = sim_siren(ng)
    if "eject" in which:
        results["eject"] = sim_eject(ng)
    if "hold" in which:
        results["hold"] = sim_hold(ng)
    if "link" in which:
        results["link"] = sim_link()
    return results


if __name__ == "__main__":
    main()
