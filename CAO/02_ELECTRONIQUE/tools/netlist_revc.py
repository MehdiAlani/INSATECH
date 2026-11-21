"""
BRC-M400 Rev C netlist - single source of truth for gen_schematic.py.

Architecture
  E-Port V2 VCC (13.8 / 17 / 24 V) -> fuse -> TVS -> LM74700 ideal diode -> VIN
  VIN -> TPS7A4101 LDO -> 11.85 V gate-drive rail
  VIN -> LMR51430 -> 3.3 V logic rail -> ferrite -> 3.3 V RF rail
  STM32U585 (Cortex-M33, PSDK armcc_cortex-m33 lib) + Semtech SX1262 + TCXO
  Actuators: ARM high-side P-MOSFET -> V_ACT, then 2 low-side channels
         (gate driver + 60 V OptiMOS + fast-decay clamp + current sense):
         fail-safe holding electromagnet, ejection solenoid
  Signalling: LED array (PWM) + siren (gate driver + 60 V OptiMOS)

Net None = no-connect.  Values marked TUNE follow Semtech reference design
E449V01A topology (AN1200.40); final values = Semtech regional BOM + VNA tuning.
"""

REVISION = "C"

# ---------------------------------------------------------------------------
# Footprints
# ---------------------------------------------------------------------------
R0402 = "Resistor_SMD:R_0402_1005Metric"
R0603 = "Resistor_SMD:R_0603_1608Metric"
R2512 = "Resistor_SMD:R_2512_6332Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
L0402 = "Inductor_SMD:L_0402_1005Metric"
L0603 = "Inductor_SMD:L_0603_1608Metric"
L0805 = "Inductor_SMD:L_0805_2012Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SOT236 = "Package_TO_SOT_SMD:SOT-23-6"
TDSON8 = "Package_TO_SOT_SMD:TDSON-8-1"
JST_GH4 = "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal"
XT30F = "Connector_AMASS:AMASS_XT30PW-F_1x02_P2.50mm_Horizontal"
HOLE = "MountingHole:MountingHole_3.2mm_M3_Pad_Via"
TUNE = "TUNE"


class Part:
    def __init__(self, ref, lib_id, value, fp, pins, mpn="", dnp=False):
        self.ref, self.lib_id, self.value, self.fp = ref, lib_id, value, fp
        self.pins = {str(k): v for k, v in pins.items()}
        self.mpn, self.dnp = mpn, dnp


def R(ref, val, a, b, fp=R0603, mpn=""):
    return Part(ref, "Device:R", val, fp, {1: a, 2: b}, mpn)


def C(ref, val, a, b, fp=C0603, mpn="", dnp=False):
    return Part(ref, "Device:C", val, fp, {1: a, 2: b}, mpn, dnp)


def L(ref, val, a, b, fp=L0402, mpn=""):
    return Part(ref, "Device:L", val, fp, {1: a, 2: b}, mpn)


def FLAG(ref, net):
    return Part(ref, "power:PWR_FLAG", "PWR_FLAG", "", {1: net})


def NFET(ref, s, g, d):
    """Infineon OptiMOS BSC028N06LS3: 60 V, 2.8 mOhm, logic level, TDSON-8."""
    return Part(ref, "Transistor_FET:BSC028N06LS3", "BSC028N06LS3", TDSON8,
                {1: s, 2: s, 3: s, 4: g, 5: d}, mpn="BSC028N06LS3GATMA1")


ROOT_NOTES = [
    "BRC-M400 Rev C - CARTE DE LARGAGE DE BOUEE + BALISE DE DETRESSE - DJI MATRICE 400",
    "",
    "Alimentation : E-Port V2 VCC (13,8 / 17 / 24 V, 5 A) -> fusible -> TVS -> diode ideale LM74700 -> VIN",
    "Conversion   : LMR51430 (36 V, 3 A, PFM) -> 3,3 V logique ; LDO TPS7A4101 (50 V) -> 11,85 V drivers de grille",
    "Calcul       : STM32U585 - Cortex-M33 160 MHz, ultra basse conso, TrustZone, crypto materielle",
    "Liaison drone: DJI PSDK V3 sur UART (lib officielle armcc_cortex-m33) -> bouton 'LARGUER' dans DJI Pilot 2",
    "Radio        : Semtech SX1262 +22 dBm + TCXO 32 MHz, 869,525 MHz (sous-bande g3, 500 mW ERP)",
    "Actionneurs  : interrupteur ARM (P-MOSFET 60 V) + electroaimant de maintien + solenoide d'ejection (UCC27511A + OptiMOS)",
    "Signalisation: LED array PWM + sirene (UCC27511A + OptiMOS 60 V 2,8 mOhm)",
    "Surete       : aimant de maintien a securite positive (aimant permanent, bobine = liberation) + double barriere ARM/FIRE",
]

SHEETS = []

# ===========================================================================
# 1. POWER
# ===========================================================================
SHEETS.append(("power", "Alimentation E-Port V2 et convertisseurs", [
    "Entree E-Port V2 VCC 13,8-24 V -> fusible 5 A -> TVS SMAJ26A -> diode ideale LM74700 + OptiMOS (perte ~17 mW a 2,5 A).",
    "LM74700 : bloque le courant inverse en < 1 us -> C3 reste charge pendant une micro-coupure du port (tenue brownout).",
    "U2 TPS7A4101 (LDO 50 V, 25 uA) : 1,173 V x (1 + 91k/10k) = 11,85 V pour les drivers de grille (Vgs 12 V -> RDS(on) nominal).",
    "U3 LMR51430 logique : 0,600 V x (1 + 100k/22,1k) = 3,315 V ; 15 uH.",
    "Rails INDEPENDANTS depuis VIN : un appel des actionneurs ne peut pas faire chuter le 3,3 V du MCU et de la radio.",
], [
    Part("J1", "Connector_Generic:Conn_01x02", "E-Port V2 VCC (XT30)",
         "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal", {1: "GND", 2: "VIN_RAW"},  # footprint silk: pin1 = "-"
         mpn="XT30PW-M"),
    Part("F1", "Device:Fuse", "5A 32V fast", "Fuse:Fuse_1206_3216Metric",
         {1: "VIN_RAW", 2: "VIN_F"}, mpn="0466005.NR"),
    Part("D1", "Diode:SMAJ26A", "SMAJ26A", "Diode_SMD:D_SMA", {1: "VIN_F", 2: "GND"}, mpn="SMAJ26A"),
    Part("U1", "Power_Management:LM74700", "LM74700-Q1", SOT236,
         {1: "VCAP_ID", 2: "GND", 3: "VIN_F", 4: "VIN", 5: "Q1_G", 6: "VIN_F"}, mpn="LM74700QDBVRQ1"),
    C("C1", "100nF 50V", "VCAP_ID", "VIN_F"),
    C("C2", "100nF 50V", "VIN_F", "GND"),
    NFET("Q1", "VIN_F", "Q1_G", "VIN"),
    Part("C3", "Device:C_Polarized", "470uF 35V low-ESR", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
         {1: "VIN", 2: "GND"}),
    # --- gate-drive rail 11.85 V (TPS7A4101: VREF 1.173 V, Cout >= 4.7 uF, Cin >= 1 uF, EN tied to IN)
    Part("U2", "Regulator_Linear:TPS7A4101DGN", "TPS7A4101",
         "Package_SO:Texas_DGN0008B_VSSOP-8-1EP_3x3mm_P0.65mm_EP2x3mm_Mask1.88x1.98mm_ThermalVias",
         {1: "+12V_GD", 2: "FB_12V", 3: None, 4: "GND", 5: "VIN", 6: None, 7: None, 8: "VIN", 9: "GND"},
         mpn="TPS7A4101DGNR"),
    C("C4", "1uF 50V X7R", "VIN", "GND", C0805),
    R("R1", "91k 1%", "+12V_GD", "FB_12V"),
    R("R2", "10k 1%", "FB_12V", "GND"),
    C("C5", "10nF", "+12V_GD", "FB_12V"),
    C("C6", "10uF 25V X7R", "+12V_GD", "GND", C1210),
    C("C7", "10uF 25V X7R", "+12V_GD", "GND", C1210),
    # --- logic rail 3.3 V
    Part("U3", "Regulator_Switching:LMR51430", "LMR51430", SOT236,
         {1: "GND", 2: "SW_3V3", 3: "VIN", 4: "FB_3V3", 5: "EN_3V3", 6: "CB_3V3"}, mpn="LMR51430XDDCR"),
    R("R4", "100k", "VIN", "EN_3V3"),
    C("C11", "10uF 50V X7R", "VIN", "GND", C1210),
    C("C12", "100nF 50V", "VIN", "GND"),
    C("C13", "100nF", "CB_3V3", "SW_3V3"),
    L("L2", "15uH 2.5A", "SW_3V3", "+3V3", "Inductor_SMD:L_Bourns_SRN6045TA", mpn="SRN6045TA-150M"),
    R("R5", "100k 1%", "+3V3", "FB_3V3"),
    R("R6", "22.1k 1%", "FB_3V3", "GND"),
    C("C14", "22uF 10V X5R", "+3V3", "GND", C1210),
    C("C15", "22uF 10V X5R", "+3V3", "GND", C1210),
    # --- RF rail isolation
    Part("FB1", "Device:FerriteBead", "600R@100MHz", L0603, {1: "+3V3", 2: "+3V3_RF"}, mpn="BLM18PG600SN1D"),
    C("C16", "10uF 10V", "+3V3_RF", "GND", C0805),
    C("C17", "100nF", "+3V3_RF", "GND"),
    # --- supervisor (open-drain -> shares NRST with SWD + IWDG)
    Part("U4", "Power_Supervisor:TPS3808DBV", "TPS3808G33", SOT236,
         {1: "NRST", 2: "GND", 3: "+3V3", 4: None, 5: "+3V3", 6: "+3V3"}, mpn="TPS3808G33DBVR"),
    C("C19", "100nF", "+3V3", "GND"),
    # --- VIN telemetry (33 V -> 3.0 V)
    R("R7", "100k 1%", "VIN", "VIN_SENSE"),
    R("R8", "10k 1%", "VIN_SENSE", "GND"),
    C("C20", "100nF", "VIN_SENSE", "GND"),
    FLAG("#FLG01", "GND"), FLAG("#FLG02", "VIN"), FLAG("#FLG03", "VIN_RAW"), FLAG("#FLG04", "+3V3"),
    FLAG("#FLG05", "+3V3_RF"), FLAG("#FLG08", "VCAP_ID"), FLAG("#FLG10", "VIN_F"),
]))

# ===========================================================================
# 2. MCU + DJI PSDK
# ===========================================================================
SHEETS.append(("mcu", "MCU STM32U585 + liaison DJI PSDK", [
    "STM32U585CIU6 : Cortex-M33 160 MHz, 2 Mo flash, 786 Ko RAM, 19 uA/MHz, TrustZone + AES/PKA materiels.",
    "PSDK : DJI fournit la lib precompilee armcc_cortex-m33 -> compilation Keil MDK (Arm Compiler 6).",
    "USART1 (PA9/PA10) 921600 bauds vers le kit E-Port V2 ; R14/R15 = protection du cable.",
    "Horloge : MSI calibre en PLL sur LSE 32,768 kHz (+/-0,25 %) -> pas de quartz HSE ; quartz CL 7 pF, C = 10 pF.",
    "ADC1 : PA0 VIN, PA1 I_HOLD, PA2 I_LED, PA3 I_EJECT. PWM : TIM1_CH1 maintien, TIM2_CH1 ejection, TIM15_CH1 LED. PB12 ARM.",
], [
    Part("U10", "MCU_ST_STM32U5:STM32U585CIUx", "STM32U585CIU6",
         "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm", {
             1: "+3V3", 2: None, 3: "LSE_IN", 4: "LSE_OUT", 5: None, 6: None, 7: "NRST",
             8: "GND", 9: "+3V3", 10: "VIN_SENSE", 11: "I_HOLD", 12: "I_LED", 13: "I_EJECT",
             14: "SX_NSS", 15: "SX_SCK", 16: "SX_MISO", 17: "SX_MOSI", 18: "SX_RESET",
             19: "SX_BUSY", 20: "SX_DIO1", 21: "RF_RXEN", 22: "VCAP", 23: "GND", 24: "+3V3",
             25: "ACT_ARM", 26: "SIREN_EN", 27: "LED_PWM", 28: None, 29: "HOLD_PWM",
             30: "PSDK_TX", 31: "PSDK_RX", 32: None, 33: None, 34: "SWDIO", 35: "GND",
             36: "+3V3", 37: "SWCLK", 38: "EJECT_PWM", 39: "SWO", 40: "SW_LOCK", 41: "SW_PAYLOAD",
             42: "LED_R", 43: "LED_G", 44: "BOOT0", 45: "LED_B", 46: None, 47: "GND",
             48: "+3V3", 49: "GND",
         }, mpn="STM32U585CIU6"),
    C("C30", "100nF", "+3V3", "GND", C0402),
    C("C31", "100nF", "+3V3", "GND", C0402),
    C("C32", "100nF", "+3V3", "GND", C0402),
    C("C33", "100nF", "+3V3", "GND", C0402),
    C("C34", "4.7uF", "+3V3", "GND"),
    C("C35", "1uF", "+3V3", "GND", C0402),
    C("C36", "4.7uF", "VCAP", "GND"),
    C("C37", "100nF", "NRST", "GND", C0402),
    R("R10", "10k", "BOOT0", "GND", R0402),
    Part("X1", "Device:Crystal", "32.768kHz CL7pF", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
         {1: "LSE_IN", 2: "LSE_OUT"}, mpn="ABS07-120-32.768KHZ-T"),
    C("C38", "10pF C0G", "LSE_IN", "GND", C0402),
    C("C39", "10pF C0G", "LSE_OUT", "GND", C0402),
    Part("J7", "Connector:Conn_ARM_JTAG_SWD_10", "SWD Cortex-10",
         "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical",
         {1: "+3V3", 2: "SWDIO", 3: "GND", 4: "SWCLK", 5: "GND", 6: "SWO", 7: None, 8: None,
          9: "GND", 10: "NRST"}),
    Part("D10", "Device:LED_RGBA", "LED RGB", "LED_SMD:LED_RGB_1210",
         {1: "LED_RK", 2: "LED_GK", 3: "LED_BK", 4: "+3V3"}),
    R("R11", "1k", "LED_RK", "LED_R", R0402),
    R("R12", "1k", "LED_GK", "LED_G", R0402),
    R("R13", "1k", "LED_BK", "LED_B", R0402),
    Part("J2", "Connector_Generic:Conn_01x04", "DJI PSDK UART", JST_GH4,
         {1: "GND", 2: "PSDK_TX_C", 3: "PSDK_RX_C", 4: None}, mpn="SM04B-GHS-TB"),
    R("R14", "100R", "PSDK_TX", "PSDK_TX_C", R0402),
    R("R15", "100R", "PSDK_RX_C", "PSDK_RX", R0402),
]))

# ===========================================================================
# 3. RADIO - Semtech SX1262 (topology of reference design E449V01A)
# ===========================================================================
SHEETS.append(("radio", "Radio LoRa Semtech SX1262 - 868 MHz", [
    "SX1262 : +22 dBm, -148 dBm de sensibilite, 4,6 mA en RX. Topologie = design de reference Semtech E449V01A (AN1200.40).",
    "Option C du datasheet : DC-DC pour le coeur (L20 15 uH entre DCC_SW et VREG), VDD_IN alimente par VBAT pour le PA.",
    "TCXO 32 MHz sinus ecrete alimente par DIO3 (SetDIO3AsTCXOCtrl), relie a XTA par 220 Ohm + 10 pF ; XTB en l'air (datasheet 4.1.4).",
    "TX : L22/C59 adaptation, L23//C60 rejecteur H2, pi C61-L24-C63, C62 blocage DC. RX : balun C64/L25/C66 (+C65 option).",
    "!! Valeurs TUNE = nomenclature regionale Semtech E449V01A (sur demande) puis accord a l'analyseur de reseau.",
    "AS179-92LF : V1 <- DIO2 (SetDIO2AsRfSwitchCtrl, 1 en TX) ; V2 <- RF_RXEN. Verifier la table de verite Skyworks.",
], [
    Part("U20", "RF:SX1262IMLTRT", "SX1262IMLTRT", "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm", {
        1: "+3V3_RF", 2: "GND", 3: "XTA", 4: None, 5: "GND", 6: "SX_DIO3", 7: "SX_VREG", 8: "GND",
        9: "SX_DCC", 10: "+3V3_RF", 11: "+3V3_RF", 12: "SX_DIO2", 13: "SX_DIO1", 14: "SX_BUSY",
        15: "SX_RESET", 16: "SX_MISO", 17: "SX_MOSI", 18: "SX_SCK", 19: "SX_NSS", 20: "GND",
        21: "RFI_P", 22: "RFI_N", 23: "RFO", 24: "VR_PA", 25: "GND",
    }, mpn="SX1262IMLTRT"),
    C("C50", "100nF", "+3V3_RF", "GND", C0402),
    C("C51", "100nF", "+3V3_RF", "GND", C0402),
    C("C52", "100nF", "+3V3_RF", "GND", C0402),
    C("C53", "10uF", "+3V3_RF", "GND", C0805),
    C("C54", "470nF", "SX_VREG", "GND", C0402),
    L("L20", "15uH 150mA", "SX_DCC", "SX_VREG", L0805),
    # --- TCXO
    Part("Y20", "Oscillator:KT2520K-T", "TCXO 32MHz 1.8V", "Oscillator:Oscillator_SMD_Kyocera_2520-6Pin_2.5x2.0mm",
         {1: "GND", 2: None, 3: "GND", 4: "TCXO_OUT", 5: None, 6: "TCXO_VCC"}),
    Part("FB20", "Device:FerriteBead", "600R@100MHz", L0402, {1: "SX_DIO3", 2: "TCXO_VCC"}),
    C("C55", "100nF", "TCXO_VCC", "GND", C0402),
    C("C56", "10pF C0G", "TCXO_OUT", "XTA_C", C0402),
    R("R20", "220R", "XTA_C", "XTA", R0402),
    # --- TX chain (E449V01A: C1 C2 L1 L2 C3 L3 C4 C5 C6 L4 C7)
    C("C57", "47pF", "VR_PA", "GND", C0402),
    C("C58", "1nF", "VR_PA", "GND", C0402),
    L("L21", TUNE, "VR_PA", "RF_A"),
    L("L22", TUNE, "RFO", "RF_A"),
    C("C59", TUNE, "RF_A", "GND", C0402),
    L("L23", TUNE, "RF_A", "RF_B"),
    C("C60", TUNE, "RF_A", "RF_B", C0402),
    C("C61", TUNE, "RF_B", "GND", C0402),
    C("C62", TUNE, "RF_B", "RF_C", C0402),
    L("L24", TUNE, "RF_C", "RF_TXP"),
    C("C63", TUNE, "RF_TXP", "GND", C0402),
    # --- RX balun (E449V01A: C11 C12 C13 L6)
    C("C64", TUNE, "RFI_N", "RF_RXP", C0402),
    C("C65", TUNE, "RF_RXP", "GND", C0402),
    L("L25", TUNE, "RFI_N", "RFI_P"),
    C("C66", TUNE, "RFI_P", "GND", C0402),
    # --- T/R switch
    Part("U21", "RF_Switch:AS179-92LF", "AS179-92LF", "Package_TO_SOT_SMD:SOT-363_SC-70-6",
         {1: "RF_RXP", 2: "GND", 3: "RF_TXP", 4: "RFSW_V1", 5: "RF_ANT", 6: "RFSW_V2"}, mpn="AS179-92LF"),
    R("R21", "100R", "SX_DIO2", "RFSW_V1", R0402),
    C("C67", "1nF", "RFSW_V1", "GND", C0402),
    R("R22", "100R", "RF_RXEN", "RFSW_V2", R0402),
    C("C68", "1nF", "RFSW_V2", "GND", C0402),
    # --- antenna pi network (E449V01A: C8 C9 L5 C10)
    C("C69", "47pF C0G", "RF_ANT", "RF_ANT2", C0402),
    C("C70", "DNP", "RF_ANT2", "GND", C0402, dnp=True),
    R("R23", "0R", "RF_ANT2", "RF_OUT", R0402),
    C("C71", "DNP", "RF_OUT", "GND", C0402, dnp=True),
    Part("J20", "Connector:Conn_Coaxial", "SMA 868MHz", "Connector_Coaxial:SMA_Amphenol_132289_EdgeMount",
         {1: "RF_OUT", 2: "GND"}, mpn="132289"),
    FLAG("#FLG20", "TCXO_VCC"),
]))

# ===========================================================================
# 4. ACTUATORS - ARM switch, holding electromagnet, ejection solenoid, LED array, siren
# ===========================================================================


def coil_channel(n, drv, fet, shunt, ina, pwm, gate, src, drain, clampk, isense, refs):
    """Low-side PWM channel for a 24 V coil on V_ACT: UCC27511A + OptiMOS,
    fast-decay clamp (Schottky + 20 V TVS -> Vds max ~ VIN + 23 V < 60 V),
    10 mOhm shunt + INA181A2 (G=50 -> 2 A = 1.0 V)."""
    c_vdd, r_in, r_on, r_off, r_gpd, c_ina, r_f, c_f, d_fw, d_tvs, conn = refs
    return [
        Part(drv, "Driver_FET:UCC27511ADBV", "UCC27511A", SOT236,
             {1: "+12V_GD", 2: gate + "H", 3: gate + "L", 4: "GND", 5: "GND", 6: pwm}, mpn="UCC27511ADBVR"),
        C(c_vdd, "1uF 25V", "+12V_GD", "GND"),
        R(r_in, "100k", pwm, "GND"),
        R(r_on, "4.7R", gate + "H", gate),
        R(r_off, "1R", gate + "L", gate),
        R(r_gpd, "10k", gate, "GND"),
        NFET(fet, src, gate, drain),
        R(shunt, "10mR 1W 1%", src, "GND", R2512),
        Part(ina, "Amplifier_Current:INA181", "INA181A2 G=50", SOT236,
             {1: isense + "_RAW", 2: "GND", 3: src, 4: "GND", 5: "GND", 6: "+3V3"}, mpn="INA181A2IDBVR"),
        C(c_ina, "100nF", "+3V3", "GND"),
        R(r_f, "1k", isense + "_RAW", isense),
        C(c_f, "10nF", isense, "GND"),
        Part(d_fw, "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA", {1: clampk, 2: drain}, mpn="SS34"),
        Part(d_tvs, "Diode:SMAJ20A", "SMAJ20A", "Diode_SMD:D_SMA", {1: clampk, 2: "V_ACT"}, mpn="SMAJ20A"),
        Part(conn, "Connector_Generic:Conn_01x02", n + " (XT30)", XT30F, {1: drain, 2: "V_ACT"}, mpn="XT30PW-F"),
    ]


SHEETS.append(("loads", "Actionneurs de largage et signalisation", [
    "ARM : Q30 SUD50P06-15 (P-MOSFET -60 V, 15 mOhm) alimente V_ACT. Vgs = -VIN x 10k/(10k+10k) = -12 V a 24 V (max -20 V).",
    "Un largage exige ARM (cote haut) ET FIRE (cote bas) : un seul defaut (GPIO, MOSFET en court-circuit) ne peut PAS lacher la bouee.",
    "MAINTIEN : electroaimant a SECURITE POSITIVE (aimant permanent ; bobine alimentee = liberation). Perte d'energie -> bouee TENUE.",
    "EJECTION : solenoide pousseur 24 V, impulsion PWM 'peak & hold' (TIM2). Confirmation par la signature de courant (creux en fin de course).",
    "Roue libre rapide D + TVS 20 V : V drain max = VIN + 0,5 + 23 V ~ 48 V < 60 V ; demagnetisation ~5x plus rapide qu'une diode seule.",
    "LED ARRAY (PWM 20 kHz) et SIRENE : meme driver UCC27511A + OptiMOS, alimentes en VIN ; allumes APRES confirmation du largage.",
    "Toutes les entrees de driver et les grilles ont un rappel a la masse : reset MCU -> TOUT est eteint, la bouee reste tenue.",
], [
    # --- ARM high-side switch -> V_ACT
    Part("Q30", "Transistor_FET:SUD50P06-15", "SUD50P06-15", "Package_TO_SOT_SMD:TO-252-2",
         {1: "ARM_G", 2: "V_ACT", 3: "VIN"}, mpn="SUD50P06-15-GE3"),
    R("R30", "10k", "VIN", "ARM_G"),
    R("R33", "10k", "ARM_G", "ARM_C"),
    Part("Q31", "Transistor_BJT:MMBT3904", "MMBT3904", SOT23, {1: "ARM_B", 2: "GND", 3: "ARM_C"}),
    R("R34", "10k", "ACT_ARM", "ARM_B"),
    R("R35", "100k", "ARM_B", "GND"),
    Part("C80", "Device:C_Polarized", "100uF 35V", "Capacitor_SMD:CP_Elec_8x10", {1: "V_ACT", 2: "GND"}),
    C("C81", "10uF 50V X7R", "V_ACT", "GND", C1210),
] + coil_channel("MAINTIEN", "U34", "Q34", "R50", "U30", "HOLD_PWM", "HOLD_G", "HOLD_SRC", "HOLD_N",
                 "HOLD_K", "I_HOLD", ["C87", "R46", "R47", "R48", "R49", "C88", "R36", "C82", "D32", "D33", "J33"])
  + coil_channel("EJECTION", "U35", "Q35", "R55", "U36", "EJECT_PWM", "EJ_G", "EJ_SRC", "EJ_N",
                 "EJ_K", "I_EJECT", ["C89", "R51", "R52", "R53", "R54", "C92", "R37", "C93", "D34", "D35", "J34"])
  + [
    # --- LED array, PWM
    Part("U31", "Driver_FET:UCC27511ADBV", "UCC27511A", SOT236,
         {1: "+12V_GD", 2: "LEDA_GH", 3: "LEDA_GL", 4: "GND", 5: "GND", 6: "LED_PWM"}, mpn="UCC27511ADBVR"),
    C("C83", "1uF 25V", "+12V_GD", "GND"),
    R("R38", "100k", "LED_PWM", "GND"),
    R("R31", "4.7R", "LEDA_GH", "LEDA_G"),
    R("R32", "1R", "LEDA_GL", "LEDA_G"),
    R("R39", "10k", "LEDA_G", "GND"),
    NFET("Q32", "LEDA_SRC", "LEDA_G", "LEDA_N"),
    R("R40", "10mR 1W 1%", "LEDA_SRC", "GND", R2512),
    Part("U32", "Amplifier_Current:INA181", "INA181A2 G=50", SOT236,
         {1: "ILED_RAW", 2: "GND", 3: "LEDA_SRC", 4: "GND", 5: "GND", 6: "+3V3"}, mpn="INA181A2IDBVR"),
    C("C84", "100nF", "+3V3", "GND"),
    R("R41", "1k", "ILED_RAW", "I_LED"),
    C("C85", "10nF", "I_LED", "GND"),
    Part("D30", "Device:D_Schottky", "SS54", "Diode_SMD:D_SMC", {1: "VIN", 2: "LEDA_N"}, mpn="SS54"),
    Part("J31", "Connector_Generic:Conn_01x02", "LED ARRAY (XT30)", XT30F, {1: "LEDA_N", 2: "VIN"}, mpn="XT30PW-F"),
    # --- siren
    Part("U33", "Driver_FET:UCC27511ADBV", "UCC27511A", SOT236,
         {1: "+12V_GD", 2: "SIR_GH", 3: "SIR_GL", 4: "GND", 5: "GND", 6: "SIREN_EN"}, mpn="UCC27511ADBVR"),
    C("C86", "1uF 25V", "+12V_GD", "GND"),
    R("R42", "100k", "SIREN_EN", "GND"),
    R("R43", "4.7R", "SIR_GH", "SIR_G"),
    R("R44", "1R", "SIR_GL", "SIR_G"),
    R("R45", "10k", "SIR_G", "GND"),
    NFET("Q33", "GND", "SIR_G", "SIREN_N"),
    Part("D31", "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA", {1: "VIN", 2: "SIREN_N"}, mpn="SS34"),
    Part("J32", "Connector_Generic:Conn_01x02", "SIRENE (XT30)", XT30F, {1: "SIREN_N", 2: "VIN"}, mpn="XT30PW-F"),
    FLAG("#FLG30", "V_ACT"),
]))

# ===========================================================================
# 5. I/O
# ===========================================================================
SHEETS.append(("io", "Capteurs et fixation", [
    "J6 : micro-rupteurs verrou ferme / presence bouee. Pull-up 10k + filtre RC 1k/100nF (anti-rebond + ESD cable).",
    "H1-H4 : M3, relies a GND (blindage + dissipation via la structure).",
], [
    Part("J6", "Connector_Generic:Conn_01x04", "SW verrou / presence", JST_GH4,
         {1: "GND", 2: "SW_LOCK_C", 3: "SW_PAYLOAD_C", 4: "GND"}, mpn="SM04B-GHS-TB"),
    R("R60", "10k", "+3V3", "SW_LOCK_C"),
    R("R61", "10k", "+3V3", "SW_PAYLOAD_C"),
    R("R62", "1k", "SW_LOCK_C", "SW_LOCK"),
    R("R63", "1k", "SW_PAYLOAD_C", "SW_PAYLOAD"),
    C("C90", "100nF", "SW_LOCK", "GND"),
    C("C91", "100nF", "SW_PAYLOAD", "GND"),
    Part("H1", "Mechanical:MountingHole_Pad", "M3", HOLE, {1: "GND"}),
    Part("H2", "Mechanical:MountingHole_Pad", "M3", HOLE, {1: "GND"}),
    Part("H3", "Mechanical:MountingHole_Pad", "M3", HOLE, {1: "GND"}),
    Part("H4", "Mechanical:MountingHole_Pad", "M3", HOLE, {1: "GND"}),
]))

# Nets deliberately shared between sheets. gen_schematic.py refuses to build if
# any other net name appears on two sheets (that is how rev B silently merged the
# RGB-LED green GPIO "LED_G" with the LED-array MOSFET gate).
GLOBAL_NETS = {
    "GND", "VIN", "+3V3", "+3V3_RF", "+12V_GD", "NRST", "VIN_SENSE",
    "ACT_ARM", "HOLD_PWM", "EJECT_PWM", "LED_PWM", "SIREN_EN", "I_HOLD", "I_EJECT", "I_LED",
    "SW_LOCK", "SW_PAYLOAD", "RF_RXEN",
    "SX_BUSY", "SX_DIO1", "SX_MISO", "SX_MOSI", "SX_NSS", "SX_RESET", "SX_SCK",
}
