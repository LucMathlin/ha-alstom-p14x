"""Constants for the Alstom P14x integration."""

DOMAIN = "alstom_p14x"

# Config keys
CONF_SLAVE_ID = "slave_id"
CONF_SCAN_INTERVAL_FAST = "scan_interval_fast"
CONF_SCAN_INTERVAL_MEDIUM = "scan_interval_medium"
CONF_SCAN_INTERVAL_SLOW = "scan_interval_slow"
CONF_ENABLE_CB_STATUS = "enable_cb_status"
CONF_ENABLE_CB_CONTROL = "enable_cb_control"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL_FAST = 1
DEFAULT_SCAN_INTERVAL_MEDIUM = 15
DEFAULT_SCAN_INTERVAL_SLOW = 60

# CB Trip/Close command register (holding register 4x00021)
# Modbus address = 21 - 1 = 20 (0-based)
REG_CB_COMMAND = 20

# Command values (standard Courier protocol)
CB_COMMAND_TRIP = 1
CB_COMMAND_CLOSE = 2

# Password register (holding register 4x00023-00024)
REG_PASSWORD = 22  # 0-based

# ============================================================
# FAST POLLING REGISTERS (Input registers, function code 04)
# All addresses are 0-based (register address - 1)
# ============================================================

# Relay Status (3x00001-00002) - 2 registers
REG_RELAY_STATUS = 0

# Plant Status (3x00002) - 1 register (CB open/closed)
REG_PLANT_STATUS = 1

# Control Status (3x00004) - 1 register
REG_CONTROL_STATUS = 3

# Active Group (3x00006) - 1 register
REG_ACTIVE_GROUP = 5

# Opto Input Status (3x00007) - 1 register
REG_OPTO_INPUT_STATUS = 6

# Relay Output Status (3x00008-00009) - 2 registers
REG_RELAY_OUTPUT_STATUS = 7

# Access Level (3x00010) - 1 register
REG_ACCESS_LEVEL = 9

# Alarm Status 1 (3x00011-00012) - 2 registers
REG_ALARM_STATUS_1 = 10

# Alarm Status 2 (3x00013-00014) - 2 registers
REG_ALARM_STATUS_2 = 12

# Alarm Status 3 (3x00015-00016) - 2 registers
REG_ALARM_STATUS_3 = 14

# ============================================================
# MEDIUM POLLING REGISTERS (Input registers, function code 04)
# Measurements 1 - Currents and Voltages
# ============================================================

# IA RMS (3x00224-00225) - 2 registers, Courier Number (current)
REG_IA_RMS = 223

# IB RMS (3x00226-00227) - 2 registers
REG_IB_RMS = 225

# IC RMS (3x00228-00229) - 2 registers
REG_IC_RMS = 227

# IN Measured Magnitude (3x00209-00210) - 2 registers
REG_IN_MEASURED = 208

# VAN RMS (3x00257-00258) - 2 registers, Courier Number (voltage)
REG_VAN_RMS = 256

# VBN RMS (3x00259-00260) - 2 registers
REG_VBN_RMS = 258

# VCN RMS (3x00261-00262) - 2 registers
REG_VCN_RMS = 260

# Frequency (3x00263) - 1 register, Courier Number (frequency)
REG_FREQUENCY = 262

# 3Ph Power Factor (3x00336) - 1 register
REG_POWER_FACTOR = 335

# Thermal State (3x00434) - 1 register, Courier Number (percentage)
REG_THERMAL_STATE = 433

# DC Supply Magnitude (3x00239-00240) - 2 registers
REG_DC_SUPPLY = 238

# ============================================================
# MEDIUM POLLING - Power (IEEE floating point, 2 registers each)
# ============================================================

# 3 Phase Watts IEEE (3x00406-00407)
REG_3PH_WATTS_IEEE = 405

# 3 Phase VArs IEEE (3x00408-00409)
REG_3PH_VARS_IEEE = 407

# ============================================================
# SLOW POLLING REGISTERS
# ============================================================

# 3Ph Watt Hours Forward IEEE (3x00412-00413)
REG_WH_FWD_IEEE = 411

# 3Ph Watt Hours Reverse IEEE (3x00414-00415)
REG_WH_REV_IEEE = 413

# 3Ph VAr Hours Forward IEEE (3x00416-00417)
REG_VARH_FWD_IEEE = 415

# 3Ph VAr Hours Reverse IEEE (3x00418-00419)
REG_VARH_REV_IEEE = 417

# CB Operations count (3x00600) - 1 register, unsigned integer
REG_CB_OPERATIONS = 599

# CB Operate Time (3x00607) - 1 register
REG_CB_OPERATE_TIME = 606

# ============================================================
# FAULT RECORD REGISTERS (View Records column)
# ============================================================

# Number of fault records stored (Modbus only)
# From the View Records section - this is at 3x00100
REG_FAULT_RECORD_COUNT = 99

# Select Fault register (to select which fault to read) - 3x00103
REG_SELECT_FAULT = 102

# Faulted Phase (3x00107) - 1 register
REG_FAULTED_PHASE = 106

# Trip Elements 1 (3x00108-00109) - 2 registers
REG_TRIP_ELEMENTS_1 = 107

# Trip Elements 2 (3x00110-00111) - 2 registers
REG_TRIP_ELEMENTS_2 = 109

# Fault Time (3x00111) - 4 registers (G12A time format)
REG_FAULT_TIME = 110

# Fault Duration (3x00114)
REG_FAULT_DURATION = 113

# CB Operate Time in fault record (3x00115)
REG_FAULT_CB_OPERATE_TIME = 114

# Fault currents
REG_FAULT_IA = 117  # 3x00118
REG_FAULT_IB = 119  # 3x00120
REG_FAULT_IC = 121  # 3x00122
