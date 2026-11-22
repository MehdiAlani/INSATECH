# -*- coding: utf-8 -*-
"""Build netlist_revd.py from netlist_revc.py.

Rev D: autonomous pod - NO electrical link to the drone at all.
  - E-Port input, DJI PSDK UART and the 24 V assumption are removed
  - 3S LiPo 2200 mAh + BQ76920 BMS + USB-C PD charging (BQ24610)
  - gate-drive rail now boosted from 3.3 V (works at any battery voltage)
  - command is LoRa only
"""
import io
import os
import re

SRC = "netlist_revc.py"
DST = "netlist_revd.py"
s = io.open(SRC, encoding="utf-8").read()


def sub(a, b, n=1):
    global s
    assert s.count(a) >= 1, "NOT FOUND:\n" + a[:200]
    s = s.replace(a, b, n)


# ---------------------------------------------------------------- header
sub('"""\nBRC-M400 Rev C netlist', '"""\nBRC-M400 Rev D netlist')
sub('''Architecture
  E-Port V2 VCC (13.8 / 17 / 24 V) -> fuse -> TVS -> LM74700 ideal diode -> VIN
  VIN -> TPS7A4101 LDO -> 11.85 V gate-drive rail
  VIN -> LMR51430 -> 3.3 V logic rail -> ferrite -> 3.3 V RF rail
  STM32U585 (Cortex-M33, PSDK armcc_cortex-m33 lib) + Semtech SX1262 + TCXO''',
    '''Architecture - AUTONOMOUS POD, no electrical interface with the drone
  3S LiPo 2200 mAh -> BQ76920 BMS (protection + balancing) -> PACK -> fuse -> TVS
                   -> LM74700 ideal diode (reverse battery) -> VIN (9.0 - 12.6 V)
  USB-C PD (STUSB4500, 20 V) -> BQ24610 synchronous buck charger -> 12.6 V / 2 A
  VIN -> LMR51430 -> 3.3 V logic rail -> ferrite -> 3.3 V RF rail
  +3V3 -> TPS61040 boost -> 12 V gate-drive rail (independent of battery state)
  STM32U585 (Cortex-M33) + Semtech SX1262 + TCXO - command over LoRa only''')
sub('REVISION = "C"', 'REVISION = "D"')

# ---------------------------------------------------------------- footprints
sub('HOLE = "MountingHole:MountingHole_3.2mm_M3_Pad_Via"',
    '''HOLE = "MountingHole:MountingHole_3.2mm_M3_Pad_Via"
XH4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
XT30M = "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal"
SOT235 = "Package_TO_SOT_SMD:SOT-23-5"
TSSOP20 = "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm"
VQFN24 = "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm"
QFN24 = "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.8x2.8mm"
USBC6 = "Connector_USB:USB_C_Receptacle_GCT_USB4085"''')

# ---------------------------------------------------------------- root notes
a = s.index("ROOT_NOTES = [")
b = s.index("]", s.index("Surete", a))
sub(s[a:b + 1], '''ROOT_NOTES = [
    "BRC-M400 Rev D - LARGAGE DE BOUEE + BALISE DE DETRESSE - MODULE AUTONOME",
    "",
    "Autonomie    : AUCUNE liaison electrique avec le drone. Le module porte son energie et sa radio.",
    "Energie      : pack 3S LiPo 2200 mAh (9,0 - 12,6 V) + BMS BQ76920 (protection cellule + equilibrage)",
    "Recharge     : USB-C Power Delivery (STUSB4500, 20 V) -> chargeur a decoupage BQ24610, 12,6 V / 2 A",
    "Calcul       : STM32U585 - Cortex-M33 160 MHz, ultra basse conso, TrustZone, crypto materielle",
    "Commande     : Semtech SX1262 +22 dBm, 869,525 MHz (sous-bande g3) - ordre de largage par liaison LoRa",
    "Actionneurs  : interrupteur ARM (P-MOSFET) + electroaimant de maintien + solenoide d'ejection 12 V",
    "Signalisation: rampe LED PWM + sirene 12 V, alimentees par la batterie APRES largage",
    "Surete       : aimant de maintien a securite positive (bobine = liberation) + double barriere ARM/FIRE",
]''')

# ---------------------------------------------------------------- power sheet
a = s.index('SHEETS.append(("power"')
b = s.index(']))', s.index('FLAG("#FLG10"', a)) + 3
sub(s[a:b], '''SHEETS.append(("power", "Alimentation batterie et convertisseurs", [
    "Entree = PACK_P, sortie du BMS (feuille 6) -> fusible 10 A -> TVS SMAJ16A -> diode ideale LM74700.",
    "LM74700 + OptiMOS : protection contre l'inversion du pack et blocage du courant inverse en < 1 us.",
    "U3 LMR51430 : 0,600 V x (1 + 100k/22,1k) = 3,315 V ; 15 uH. Fonctionne sur toute la plage du pack.",
    "U2 TPS61040 : elevateur 3,3 V -> 11,96 V pour les drivers de grille. Il ne depend PAS de la tension pack,",
    "              donc Vgs reste nominal meme a 9 V batterie (c'est ce qu'un LDO 12 V ne saurait pas faire).",
    "VIN_SENSE : pont 100k/30k -> 2,91 V a 12,6 V, pour la jauge et la coupure basse tension.",
], [
    Part("F1", "Device:Fuse", "10A 32V", "Fuse:Fuse_1206_3216Metric",
         {1: "PACK_P", 2: "VBAT_F"}, mpn="0466010.NR"),
    Part("D1", "Diode:SMAJ16A", "SMAJ16A", "Diode_SMD:D_SMA", {1: "VBAT_F", 2: "GND"}, mpn="SMAJ16A"),
    Part("U1", "Power_Management:LM74700", "LM74700-Q1", SOT236,
         {1: "VCAP_ID", 2: "GND", 3: "VBAT_F", 4: "VIN", 5: "Q1_G", 6: "VBAT_F"}, mpn="LM74700QDBVRQ1"),
    C("C1", "100nF 50V", "VCAP_ID", "VBAT_F"),
    C("C2", "100nF 50V", "VBAT_F", "GND"),
    NFET("Q1", "VBAT_F", "Q1_G", "VIN"),
    Part("C3", "Device:C_Polarized", "470uF 25V low-ESR", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
         {1: "VIN", 2: "GND"}),
    # --- logic rail 3.3 V (buck, works down to 9 V pack)
    Part("U3", "Regulator_Switching:LMR51430", "LMR51430", SOT236,
         {1: "GND", 2: "SW_3V3", 3: "VIN", 4: "FB_3V3", 5: "EN_3V3", 6: "CB_3V3"}, mpn="LMR51430XDDCR"),
    R("R4", "100k", "VIN", "EN_3V3"),
    C("C11", "10uF 25V X7R", "VIN", "GND", C1210),
    C("C12", "100nF 50V", "VIN", "GND"),
    C("C13", "100nF", "CB_3V3", "SW_3V3"),
    L("L2", "15uH 2.5A", "SW_3V3", "+3V3", "Inductor_SMD:L_Bourns_SRN6045TA", mpn="SRN6045TA-150M"),
    R("R5", "100k 1%", "+3V3", "FB_3V3"),
    R("R6", "22.1k 1%", "FB_3V3", "GND"),
    C("C14", "22uF 10V X5R", "+3V3", "GND", C1210),
    C("C15", "22uF 10V X5R", "+3V3", "GND", C1210),
    # --- gate-drive rail: BOOST from 3.3 V, so Vgs stays nominal at any pack voltage
    #     TPS61040 FB = 1.233 V -> 1.233 x (1 + 1M/113k) = 11.96 V
    Part("U2", "Regulator_Switching:TPS61040DBV", "TPS61040", SOT235,
         {1: "SW_12V", 2: "GND", 3: "FB_12V", 4: "+3V3", 5: "+3V3"}, mpn="TPS61040DBVR"),
    L("L1", "10uH", "+3V3", "SW_12V", L0805, mpn="LQH3NPN100MJ0"),
    Part("D2", "Device:D_Schottky", "MBR0540", "Diode_SMD:D_SOD-123",
         {1: "SW_12V", 2: "+12V_GD"}, mpn="MBR0540T1G"),
    R("R1", "1M 1%", "+12V_GD", "FB_12V"),
    R("R2", "113k 1%", "FB_12V", "GND"),
    C("C5", "10pF", "+12V_GD", "FB_12V", C0402),
    C("C6", "10uF 25V X7R", "+12V_GD", "GND", C1210),
    C("C7", "4.7uF 25V X7R", "+12V_GD", "GND", C0805),
    C("C4", "10uF 10V X7R", "+3V3", "GND", C0805),
    # --- RF rail isolation
    Part("FB1", "Device:FerriteBead", "600R@100MHz", L0603, {1: "+3V3", 2: "+3V3_RF"}, mpn="BLM18PG600SN1D"),
    C("C16", "10uF 10V", "+3V3_RF", "GND", C0805),
    C("C17", "100nF", "+3V3_RF", "GND"),
    # --- supervisor (open-drain -> shares NRST with SWD + IWDG)
    Part("U4", "Power_Supervisor:TPS3808DBV", "TPS3808G33", SOT236,
         {1: "NRST", 2: "GND", 3: "+3V3", 4: None, 5: "+3V3", 6: "+3V3"}, mpn="TPS3808G33DBVR"),
    C("C19", "100nF", "+3V3", "GND"),
    # --- pack telemetry (12.6 V -> 2.91 V)
    R("R7", "100k 1%", "VIN", "VIN_SENSE"),
    R("R8", "30k 1%", "VIN_SENSE", "GND"),
    C("C20", "100nF", "VIN_SENSE", "GND"),
    FLAG("#FLG01", "GND"), FLAG("#FLG02", "VIN"), FLAG("#FLG03", "VBAT_F"), FLAG("#FLG04", "+3V3"),
    FLAG("#FLG05", "+3V3_RF"), FLAG("#FLG08", "VCAP_ID"), FLAG("#FLG11", "+12V_GD"),
]))''')

# ---------------------------------------------------------------- MCU: drop PSDK, add I2C
sub('"PSDK : DJI fournit la lib precompilee armcc_cortex-m33 -> compilation Keil MDK (Arm Compiler 6).",\n',
    '"Module AUTONOME : aucune liaison avec le controleur de vol. L\'ordre de largage arrive par LoRa.",\n')
sub('"USART1 (PA9/PA10) 921600 bauds vers le kit E-Port V2 ; R14/R15 = protection du cable.",\n',
    '"I2C (PA9/PA10, instance a confirmer sous CubeMX) : BMS BQ76920 + STUSB4500 ; repli I2C logiciel possible.",\n')
sub('"ADC1 : PA0 VIN, PA1 I_HOLD, PA2 I_LED, PA3 I_EJECT. PWM : TIM1_CH1 maintien, TIM2_CH1 ejection, TIM15_CH1 LED. PB12 ARM.",',
    '"ADC1 : PA0 pack, PA1 I_HOLD, PA2 I_LED, PA3 I_EJECT. PWM : TIM1_CH1 maintien, TIM2_CH1 ejection, TIM15_CH1 LED. PB12 ARM.",')
sub('30: "PSDK_TX", 31: "PSDK_RX", 32: None, 33: None,',
    '30: "I2C_SCL", 31: "I2C_SDA", 32: "BMS_ALERT", 33: "CHG_STAT",')
sub('''    Part("J2", "Connector_Generic:Conn_01x04", "DJI PSDK UART", JST_GH4,
         {1: "GND", 2: "PSDK_TX_C", 3: "PSDK_RX_C", 4: None}, mpn="SM04B-GHS-TB"),
    R("R14", "100R", "PSDK_TX", "PSDK_TX_C", R0402),
    R("R15", "100R", "PSDK_RX_C", "PSDK_RX", R0402),
''',
    '''''')

# ---------------------------------------------------------------- loads: 12 V actuators
sub('"ARM : Q30 SUD50P06-15 (P-MOSFET -60 V, 15 mOhm) alimente V_ACT. Vgs = -VIN x 10k/(10k+10k) = -12 V a 24 V (max -20 V).",',
    '"ARM : Q30 SUD50P06-15 (P-MOSFET -60 V, 15 mOhm) alimente V_ACT. Vgs = -VIN/2 = -4,5 a -6,3 V : suffisant (Vgs(th) max -4 V).",')
sub('"EJECTION : solenoide pousseur 24 V, impulsion PWM \'peak & hold\' (TIM2). Confirmation par la signature de courant (creux en fin de course).",',
    '"EJECTION : solenoide pousseur 12 V, impulsion PWM \'peak & hold\' (TIM2). Confirmation par la signature de courant (creux en fin de course).",')
sub('"Roue libre rapide D + TVS 20 V : V drain max = VIN + 0,5 + 23 V ~ 48 V < 60 V ; demagnetisation ~5x plus rapide qu\'une diode seule.",',
    '"Roue libre rapide D + TVS 20 V : V drain max = 12,6 + 0,5 + 23 ~ 36 V < 60 V ; demagnetisation ~5x plus rapide qu\'une diode seule.",')
sub('"LED ARRAY (PWM 20 kHz) et SIRENE : meme driver UCC27511A + OptiMOS, alimentes en VIN ; allumes APRES confirmation du largage.",',
    '"LED ARRAY (PWM 20 kHz) et SIRENE 12 V : meme driver UCC27511A + OptiMOS, alimentes par la batterie ; allumes APRES le largage.",')
sub('"LED ARRAY (XT30)"', '"LED ARRAY 12V (XT30)"')
sub('"SIRENE (XT30)"', '"SIRENE 12V (XT30)"')
sub('n + " (XT30)"', 'n + " 12V (XT30)"')      # MAINTIEN / EJECTION built by coil_channel()

# ---------------------------------------------------------------- drop the DNP antenna tuning caps
sub("""    C("C70", "DNP", "RF_ANT2", "GND", C0402, dnp=True),
    R("R23", "0R", "RF_ANT2", "RF_OUT", R0402),
    C("C71", "DNP", "RF_OUT", "GND", C0402, dnp=True),
""",
    """    R("R23", "0R", "RF_ANT2", "RF_OUT", R0402),
""")

# ---------------------------------------------------------------- new sheet: battery
sub("GLOBAL_NETS = {", BATT_SHEET := '''# ===========================================================================
# 6. BATTERIE 3S + CHARGE USB-C PD + BMS
# ===========================================================================
SHEETS.append(("batterie", "Batterie 3S, BMS et charge USB-C", [
    "Pack 3S LiPo 2200 mAh (9,0 - 12,6 V, 24,4 Wh). Equilibrage et mesure cellule par cellule.",
    "U40 STUSB4500 : negociation USB-C Power Delivery autonome (20 V) - fonctionne meme MCU eteint.",
    "U41 BQ24610 : chargeur a decoupage synchrone. VFB 2,1 V x (1 + 100k/20k) = 12,6 V ; 2 A (1C) avec Rsn 10 mOhm.",
    "U42 BQ76920 : AFE 3S - surcharge, decharge profonde, surintensite, court-circuit, temperature, equilibrage.",
    "Protection materielle AUTONOME : les MOSFET CHG/DSG coupent le pack sans intervention du MCU.",
    "Le MCU lit l'etat du pack en I2C (tension par cellule, courant, temperature) et le renvoie par LoRa.",
    "4 LED d'etat : charge en cours, fin de charge/defaut, USB-C PD etabli, alerte BMS.",
], [
    # ---------------- USB-C receptacle + PD sink
    Part("J40", "Connector:USB_C_Receptacle_PowerOnly_24P", "USB-C charge", USBC6,
         {"A1": "GND", "A4": "VBUS", "A5": "CC1", "A9": "VBUS", "A12": "GND",
          "B1": "GND", "B4": "VBUS", "B5": "CC2", "B9": "VBUS", "B12": "GND",
          "SH": "GND"}, mpn="USB4085-GF-A"),
    C("C100", "10uF 25V X7R", "VBUS", "GND", C1210),
    C("C101", "100nF", "VBUS", "GND"),
    Part("U40", "Interface_USB:STUSB4500QTR", "STUSB4500", QFN24,
         {1: None, 2: "CC1", 3: None, 4: "CC2", 5: None, 6: "PD_RESET", 7: "I2C_SCL",
          8: "I2C_SDA", 9: "VBUS_DISCH", 10: "GND", 11: None, 12: "GND", 13: "GND",
          14: None, 15: None, 16: None, 17: None, 18: "VBUS_VS", 19: None,
          20: "PD_OK", 21: "VREG_1V2", 22: "VBUS", 23: "VREG_2V7", 24: "VBUS", 25: "GND"},
         mpn="STUSB4500QTR"),
    C("C102", "1uF", "VREG_1V2", "GND", C0402),
    C("C103", "1uF", "VREG_2V7", "GND", C0402),
    C("C104", "100nF", "VBUS", "GND", C0402),
    R("R100", "10k", "PD_RESET", "GND", R0402),
    R("R101", "1M", "VBUS", "VBUS_VS", R0402),
    R("R102", "100k", "VBUS_VS", "GND", R0402),
    Part("Q44", "Transistor_FET:BSS84", "BSS84", SOT23, {1: "VBUS_DISCH", 2: "GND", 3: "VBUS"}),
    # ---------------- charger BQ24610 : VBUS -> 12.6 V / 2 A
    Part("U41", "Battery_Management:BQ24610", "BQ24610", VQFN24,
         {1: "CHG_ACN", 2: "CHG_ACP", 3: None, 4: "GND", 5: "CHG_STAT1", 6: "CHG_TS",
          7: "CHG_TTC", 8: "CHG_STAT", 9: "CHG_STAT2", 10: "CHG_VREF", 11: "CHG_ISET1",
          12: "CHG_VFB", 13: "PACK_P", 14: "CHG_SRP", 15: "CHG_ISET2", 16: "CHG_ACSET",
          17: "GND", 18: "CHG_REGN", 19: "CHG_LO", 20: "CHG_PH", 21: "CHG_HI",
          22: "CHG_BTST", 23: None, 24: "VBUS", 25: "GND"}, mpn="BQ24610RGER"),
    R("R103", "10m 1%", "VBUS", "CHG_ACN", R2512, mpn="CSS2512"),
    R("R104", "10k", "CHG_ACP", "VBUS", R0402),
    C("C105", "100nF", "CHG_ACN", "CHG_ACP", C0402),
    C("C106", "10uF 25V X7R", "VBUS", "GND", C1210),
    C("C107", "1uF", "CHG_REGN", "GND", C0603),
    C("C108", "47nF", "CHG_BTST", "CHG_PH", C0402),
    NFET("Q40", "CHG_PH", "CHG_HI", "VBUS"),
    NFET("Q41", "GND", "CHG_LO", "CHG_PH"),
    L("L40", "10uH 4A", "CHG_PH", "CHG_SRP", "Inductor_SMD:L_Bourns_SRN6045TA", mpn="SRN6045TA-100M"),
    R("R105", "10m 1%", "CHG_SRP", "PACK_P", R2512, mpn="CSS2512"),
    C("C109", "22uF 25V X7R", "PACK_P", "GND", C1210),
    C("C110", "22uF 25V X7R", "PACK_P", "GND", C1210),
    # charge voltage 12.6 V : 2.1 V x (1 + 100k/20k)
    R("R106", "100k 1%", "PACK_P", "CHG_VFB"),
    R("R107", "20k 1%", "CHG_VFB", "GND"),
    R("R108", "100k 1%", "CHG_VREF", "CHG_ISET1"),
    R("R109", "100k 1%", "CHG_ISET1", "GND"),
    R("R110", "100k 1%", "CHG_VREF", "CHG_ACSET"),
    R("R111", "33k 1%", "CHG_ACSET", "GND"),
    R("R112", "100k", "CHG_ISET2", "GND"),
    C("C111", "100nF", "CHG_TTC", "GND", C0402),
    C("C112", "1uF", "CHG_VREF", "GND", C0402),
    # pack thermistor (on the pack, via the balance connector)
    Part("RT40", "Device:Thermistor_NTC", "10k NTC B3380", R0603, {1: "CHG_TS", 2: "GND"}),
    R("R113", "10k 1%", "CHG_VREF", "CHG_TS"),
    # charger output IS the pack+ node (BQ24610 regulates straight onto the pack)
    # ---------------- BMS BQ76920 (3S)
    Part("U42", "Battery_Management:BQ76920PW", "BQ76920", TSSOP20,
         {1: "BMS_DSG", 2: "BMS_CHG", 3: "BATT_N", 4: "I2C_SDA", 5: "I2C_SCL", 6: "BMS_TS",
          7: "BMS_CAP1", 8: "BMS_REGOUT", 9: "BMS_REGSRC", 10: "BMS_BAT", 11: None,
          12: "CELL3F", 13: "CELL3F", 14: "CELL3F", 15: "CELL2F", 16: "CELL1F", 17: "BATT_N",
          18: "BMS_SRP", 19: "BMS_SRN", 20: "BMS_ALERT"}, mpn="BQ76920PWR"),
    # balance connector of the pack : B- / B1 / B2 / B3
    Part("J42", "Connector_Generic:Conn_01x02", "PACK 3S (XT30)", XT30M,
         {1: "BATT_N", 2: "PACK_P"}, mpn="XT30PW-M"),
    Part("J41", "Connector_Generic:Conn_01x04", "Equilibrage 3S (XH)", XH4,
         {1: "BATT_N", 2: "CELL1", 3: "CELL2", 4: "PACK_P"}, mpn="B4B-XH-A"),
    R("R114", "1k", "CELL1", "CELL1F", R0603),
    R("R115", "1k", "CELL2", "CELL2F", R0603),
    R("R116", "1k", "PACK_P", "CELL3F", R0603),
    C("C113", "100nF 50V", "CELL1F", "BATT_N", C0603),
    C("C114", "100nF 50V", "CELL2F", "CELL1F", C0603),
    C("C115", "100nF 50V", "CELL3F", "CELL2F", C0603),
    R("R117", "100R", "CELL3F", "BMS_BAT", R0603),
    C("C116", "1uF 25V", "BMS_BAT", "BATT_N", C0603),
    R("R118", "100R", "CELL3F", "BMS_REGSRC", R0603),
    C("C117", "1uF 25V", "BMS_REGSRC", "BATT_N", C0603),
    C("C118", "1uF", "BMS_CAP1", "BATT_N", C0402),
    C("C119", "1uF", "BMS_REGOUT", "BATT_N", C0402),
    Part("RT41", "Device:Thermistor_NTC", "10k NTC B3380", R0603, {1: "BMS_TS", 2: "BATT_N"}),
    # protection MOSFETs in the pack return path (charge + discharge, back to back)
    # BAT- -> DSG -> (drains tied) -> CHG -> shunt -> system GND
    NFET("Q43", "BATT_N", "BMS_DSG", "BMS_MID"),
    NFET("Q42", "PACK_SNS", "BMS_CHG", "BMS_MID"),
    Part("R119", "Device:R_Shunt", "5m 1% 2W", "Resistor_SMD:R_2512_6332Metric",
         {1: "PACK_SNS", 2: "GND", 3: "BMS_SRP", 4: "BMS_SRN"}, mpn="WSL2512R0050FEA"),
    C("C120", "10uF 25V X7R", "PACK_P", "GND", C1210),
    # ---------------- status LEDs
    Part("D42", "Device:LED", "vert CHARGE", "LED_SMD:LED_0805_2012Metric",
         {1: "LED_CHG_K", 2: "+3V3"}),
    R("R120", "1k", "LED_CHG_K", "CHG_STAT1", R0402),
    Part("D43", "Device:LED", "orange DEFAUT", "LED_SMD:LED_0805_2012Metric",
         {1: "LED_FLT_K", 2: "+3V3"}),
    R("R121", "1k", "LED_FLT_K", "CHG_STAT2", R0402),
    Part("D44", "Device:LED", "bleu USB-C PD", "LED_SMD:LED_0805_2012Metric",
         {1: "LED_PD_K", 2: "+3V3"}),
    R("R122", "1k", "LED_PD_K", "PD_OK", R0402),
    Part("D45", "Device:LED", "rouge ALERTE BMS", "LED_SMD:LED_0805_2012Metric",
         {1: "LED_BMS_K", 2: "+3V3"}),
    R("R123", "1k", "LED_BMS_K", "BMS_ALERT", R0402),
    R("R124", "100k", "CHG_STAT1", "+3V3", R0402),
    R("R125", "100k", "CHG_STAT2", "+3V3", R0402),
    # I2C pull-ups, placed next to the two slaves (BMS + USB-C PD controller)
    R("R126", "4.7k", "I2C_SCL", "+3V3", R0402),
    R("R127", "4.7k", "I2C_SDA", "+3V3", R0402),
    FLAG("#FLG40", "VBUS"), FLAG("#FLG41", "PACK_P"), FLAG("#FLG42", "BATT_N"),
    FLAG("#FLG43", "BMS_REGSRC"), FLAG("#FLG44", "CHG_PH"), FLAG("#FLG45", "CHG_BTST"),
]))

GLOBAL_NETS = {''')

# ---------------------------------------------------------------- globals
sub('''    "SX_BUSY", "SX_DIO1", "SX_MISO", "SX_MOSI", "SX_NSS", "SX_RESET", "SX_SCK",
}''',
    '''    "SX_BUSY", "SX_DIO1", "SX_MISO", "SX_MOSI", "SX_NSS", "SX_RESET", "SX_SCK",
    "I2C_SCL", "I2C_SDA", "BMS_ALERT", "CHG_STAT", "PACK_P",
}''')

io.open(DST, "w", encoding="utf-8", newline="\n").write(s)
print("ecrit", DST, len(s), "octets")
