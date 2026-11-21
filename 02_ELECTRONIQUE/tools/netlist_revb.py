"""
BRC-M400 Rev B netlist - single source of truth for gen_schematic.py.

Architecture
  E-Port V2 VCC (13.8 / 17 / 24 V) -> fuse -> TVS -> LM74700 ideal diode -> VIN
  VIN -> LMR51430 #1 -> 6.05 V servo rail   (also feeds the gate drivers)
  VIN -> LMR51430 #2 -> 3.3 V logic rail -> ferrite -> 3.3 V RF rail
  STM32U585 (Cortex-M33, PSDK armcc_cortex-m33 lib) + Semtech SX1262 + TCXO
  Loads: 1 servo (P-MOSFET high-side + current sense),
         LED array (gate driver + 60 V OptiMOS, PWM, current sense),
         siren (gate driver + 60 V OptiMOS)

Net None = no-connect.  Values marked TUNE follow Semtech reference design
E449V01A topology (AN1200.40); final values = Semtech regional BOM + VNA tuning.
"""

REVISION = "B"

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
    "BRC-M400 Rev B - CARTE DE LARGAGE DE BOUEE + BALISE DE DETRESSE - DJI MATRICE 400",
    "",
    "Alimentation : E-Port V2 VCC (13,8 / 17 / 24 V, 5 A) -> fusible -> TVS -> diode ideale LM74700 -> VIN",
    "Conversion   : 2 x LMR51430 (36 V, 3 A, PFM 500 kHz) INDEPENDANTS : 6,05 V servo / 3,3 V logique",
    "Calcul       : STM32U585 - Cortex-M33 160 MHz, ultra basse conso, TrustZone, crypto materielle",
    "Liaison drone: DJI PSDK V3 sur UART (lib officielle armcc_cortex-m33) -> bouton 'LARGUER' dans DJI Pilot 2",
    "Radio        : Semtech SX1262 +22 dBm + TCXO 32 MHz, 869,525 MHz (sous-bande g3, 500 mW ERP)",
    "Puissance    : servo (P-MOSFET 1,9 mOhm) / LED array PWM + sirene (driver UCC27511A + OptiMOS 60 V 2,8 mOhm)",
    "Surete       : verrou non-reversible ; reset / perte d'energie / perte de liaison -> charge VERROUILLEE",
]

SHEETS = []

# ===========================================================================
# 1. POWER
# ===========================================================================
SHEETS.append(("power", "Alimentation E-Port V2 et convertisseurs", [
    "Entree E-Port V2 VCC 13,8-24 V -> fusible 5 A -> TVS SMAJ26A -> diode ideale LM74700 + OptiMOS (perte ~17 mW a 2,5 A).",
    "LM74700 : bloque le courant inverse en < 1 us -> C3 reste charge pendant une micro-coupure du port (tenue brownout).",
    "U2 servo : 0,600 V x (1 + 100k/11k) = 6,05 V ; L = (24-6) x 6 / (24 x 500 kHz x 0,9 A) = 10 uH.",
    "U3 logique : 0,600 V x (1 + 100k/22,1k) = 3,315 V ; 15 uH. Meme CI que U2 : nomenclature rationalisee.",
    "Rails INDEPENDANTS depuis VIN : un calage servo ne peut pas faire chuter le 3,3 V du MCU et de la radio.",
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
    # --- servo rail 6.05 V / 3 A
    Part("U2", "Regulator_Switching:LMR51430", "LMR51430", SOT236,
         {1: "GND", 2: "SW_6V", 3: "VIN", 4: "FB_6V", 5: "EN_6V", 6: "CB_6V"}, mpn="LMR51430XDDCR"),
    R("R1", "100k", "VIN", "EN_6V"),
    C("C4", "10uF 50V X7R", "VIN", "GND", C1210),
    C("C5", "10uF 50V X7R", "VIN", "GND", C1210),
    C("C6", "100nF 50V", "VIN", "GND"),
    C("C7", "100nF", "CB_6V", "SW_6V"),
    L("L1", "10uH 4.2A", "SW_6V", "+6V_SRV", "Inductor_SMD:L_Sunlord_SWPA8040S", mpn="SWPA8040S100MT"),
    R("R2", "100k 1%", "+6V_SRV", "FB_6V"),
    R("R3", "11k 1%", "FB_6V", "GND"),
    C("C8", "22uF 16V X5R", "+6V_SRV", "GND", C1210),
    C("C9", "22uF 16V X5R", "+6V_SRV", "GND", C1210),
    Part("C10", "Device:C_Polarized", "100uF 16V", "Capacitor_SMD:CP_Elec_6.3x7.7", {1: "+6V_SRV", 2: "GND"}),
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
    # --- gate-driver supply (RC-filtered from the 6 V rail)
    R("R9", "10R", "+6V_SRV", "+6V_GD"),
    C("C18", "10uF 16V", "+6V_GD", "GND", C0805),
    # --- supervisor (open-drain -> shares NRST with SWD + IWDG)
    Part("U4", "Power_Supervisor:TPS3808DBV", "TPS3808G33", SOT236,
         {1: "NRST", 2: "GND", 3: "+3V3", 4: None, 5: "+3V3", 6: "+3V3"}, mpn="TPS3808G33DBVR"),
    C("C19", "100nF", "+3V3", "GND"),
    # --- VIN telemetry (33 V -> 3.0 V)
    R("R7", "100k 1%", "VIN", "VIN_SENSE"),
    R("R8", "10k 1%", "VIN_SENSE", "GND"),
    C("C20", "100nF", "VIN_SENSE", "GND"),
    FLAG("#FLG01", "GND"), FLAG("#FLG02", "VIN"), FLAG("#FLG03", "VIN_RAW"), FLAG("#FLG04", "+3V3"),
    FLAG("#FLG05", "+3V3_RF"), FLAG("#FLG06", "+6V_SRV"), FLAG("#FLG07", "+6V_GD"), FLAG("#FLG08", "VCAP_ID"), FLAG("#FLG10", "VIN_F"),
]))

# ===========================================================================
# 2. MCU + DJI PSDK
# ===========================================================================
SHEETS.append(("mcu", "MCU STM32U585 + liaison DJI PSDK", [
    "STM32U585CIU6 : Cortex-M33 160 MHz, 2 Mo flash, 786 Ko RAM, 19 uA/MHz, TrustZone + AES/PKA materiels.",
    "PSDK : DJI fournit la lib precompilee armcc_cortex-m33 -> compilation Keil MDK (Arm Compiler 6).",
    "USART1 (PA9/PA10) 921600 bauds vers le kit E-Port V2 ; R14/R15 = protection du cable.",
    "Horloge : MSI calibre en PLL sur LSE 32,768 kHz (+/-0,25 %) -> pas de quartz HSE ; quartz CL 7 pF, C = 10 pF.",
    "ADC1 : PA0 VIN, PA1 I_SERVO, PA2 I_LED. TIM1_CH1 servo, TIM15_CH1 LED PWM, TIM4 LED RGB. A valider dans CubeMX.",
], [
    Part("U10", "MCU_ST_STM32U5:STM32U585CIUx", "STM32U585CIU6",
         "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm", {
             1: "+3V3", 2: None, 3: "LSE_IN", 4: "LSE_OUT", 5: None, 6: None, 7: "NRST",
             8: "GND", 9: "+3V3", 10: "VIN_SENSE", 11: "I_SERVO", 12: "I_LED", 13: None,
             14: "SX_NSS", 15: "SX_SCK", 16: "SX_MISO", 17: "SX_MOSI", 18: "SX_RESET",
             19: "SX_BUSY", 20: "SX_DIO1", 21: "RF_RXEN", 22: "VCAP", 23: "GND", 24: "+3V3",
             25: "SERVO_EN", 26: "SIREN_EN", 27: "LED_PWM", 28: None, 29: "SERVO_PWM",
             30: "PSDK_TX", 31: "PSDK_RX", 32: None, 33: None, 34: "SWDIO", 35: "GND",
             36: "+3V3", 37: "SWCLK", 38: None, 39: "SWO", 40: "SW_LOCK", 41: "SW_PAYLOAD",
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
# 4. LOADS - servo, LED array (PWM), siren
# ===========================================================================
SHEETS.append(("loads", "Puissance : servo, LED array PWM, sirene", [
    "SERVO : interrupteur cote haut Si7141DP (1,9 mOhm) -> coupure totale au repos. Mesure 25 mOhm + INA181A1 (G=20) : 2,5 A -> 1,25 V.",
    "LED ARRAY : UCC27511A (4 A / 8 A) -> OptiMOS BSC028N06LS3. PWM jusqu'a 25 kHz ; R31 4,7 Ohm a l'allumage, R32 1 Ohm a l'extinction.",
    "Mesure LED cote bas 10 mOhm + INA181A2 (G=50) : 2 A -> 1,0 V -> detection balise HS apres largage.",
    "SIRENE : meme etage de puissance, roue libre SS34 pour la charge inductive.",
    "Pull-downs sur les entrees des drivers et les grilles : TOUTES les charges ETEINTES pendant un reset MCU.",
    "Drivers alimentes par +6V_GD (filtre RC depuis le rail 6 V) : Vgs = 6 V > 4,5 V de specification RDS(on).",
], [
    # --- servo high-side switch
    Part("Q30", "Transistor_FET:Si7141DP", "Si7141DP", "Package_SO:PowerPAK_SO-8_Single",
         {1: "+6V_SRV", 2: "+6V_SRV", 3: "+6V_SRV", 4: "SRV_G", 5: "+6V_SW"}, mpn="SI7141DP-T1-GE3"),
    R("R30", "10k", "+6V_SRV", "SRV_G"),
    Part("Q31", "Transistor_BJT:MMBT3904", "MMBT3904", SOT23, {1: "SRV_B", 2: "GND", 3: "SRV_G"}),
    R("R33", "10k", "SERVO_EN", "SRV_B"),
    R("R34", "100k", "SRV_B", "GND"),
    R("R35", "25mR 1W 1%", "+6V_SW", "SERVO_V", R2512),
    Part("U30", "Amplifier_Current:INA181", "INA181A1 G=20", SOT236,
         {1: "ISRV_RAW", 2: "GND", 3: "+6V_SW", 4: "SERVO_V", 5: "GND", 6: "+3V3"}, mpn="INA181A1IDBVR"),
    C("C80", "100nF", "+3V3", "GND"),
    R("R36", "1k", "ISRV_RAW", "I_SERVO"),
    C("C81", "10nF", "I_SERVO", "GND"),
    Part("C82", "Device:C_Polarized", "220uF 10V", "Capacitor_SMD:CP_Elec_6.3x7.7", {1: "SERVO_V", 2: "GND"}),
    R("R37", "220R", "SERVO_PWM", "SERVO_SIG"),
    Part("J30", "Connector_Generic:Conn_01x03", "SERVO", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
         {1: "GND", 2: "SERVO_V", 3: "SERVO_SIG"}),
    # --- LED array, PWM
    Part("U31", "Driver_FET:UCC27511ADBV", "UCC27511A", SOT236,
         {1: "+6V_GD", 2: "LED_GH", 3: "LED_GL", 4: "GND", 5: "GND", 6: "LED_PWM"}, mpn="UCC27511ADBVR"),
    C("C83", "1uF 16V", "+6V_GD", "GND"),
    R("R38", "100k", "LED_PWM", "GND"),
    R("R31", "4.7R", "LED_GH", "LED_G"),
    R("R32", "1R", "LED_GL", "LED_G"),
    R("R39", "10k", "LED_G", "GND"),
    NFET("Q32", "LED_SRC", "LED_G", "LED_N"),
    R("R40", "10mR 1W 1%", "LED_SRC", "GND", R2512),
    Part("U32", "Amplifier_Current:INA181", "INA181A2 G=50", SOT236,
         {1: "ILED_RAW", 2: "GND", 3: "LED_SRC", 4: "GND", 5: "GND", 6: "+3V3"}, mpn="INA181A2IDBVR"),
    C("C84", "100nF", "+3V3", "GND"),
    R("R41", "1k", "ILED_RAW", "I_LED"),
    C("C85", "10nF", "I_LED", "GND"),
    Part("D30", "Device:D_Schottky", "SS54", "Diode_SMD:D_SMC", {1: "VIN", 2: "LED_N"}, mpn="SS54"),
    Part("J31", "Connector_Generic:Conn_01x02", "LED ARRAY (XT30)", XT30F, {1: "LED_N", 2: "VIN"}, mpn="XT30PW-F"),
    # --- siren
    Part("U33", "Driver_FET:UCC27511ADBV", "UCC27511A", SOT236,
         {1: "+6V_GD", 2: "SIR_GH", 3: "SIR_GL", 4: "GND", 5: "GND", 6: "SIREN_EN"}, mpn="UCC27511ADBVR"),
    C("C86", "1uF 16V", "+6V_GD", "GND"),
    R("R42", "100k", "SIREN_EN", "GND"),
    R("R43", "4.7R", "SIR_GH", "SIR_G"),
    R("R44", "1R", "SIR_GL", "SIR_G"),
    R("R45", "10k", "SIR_G", "GND"),
    NFET("Q33", "GND", "SIR_G", "SIREN_N"),
    Part("D31", "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA", {1: "VIN", 2: "SIREN_N"}, mpn="SS34"),
    Part("J32", "Connector_Generic:Conn_01x02", "SIRENE (XT30)", XT30F, {1: "SIREN_N", 2: "VIN"}, mpn="XT30PW-F"),
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
