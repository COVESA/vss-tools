# vspec unit key → QUDT QuantityKind and unit
QUDT_MAPPING: dict[str, dict[str, str]] = {
    # length
    "mm": {"qudt_uri": "http://qudt.org/vocab/unit/MilliM", "qudt_quantity_kind": "Length", "qudt_unit": "MILLIM"},
    "cm": {"qudt_uri": "http://qudt.org/vocab/unit/CentiM", "qudt_quantity_kind": "Length", "qudt_unit": "CENTIM"},
    "m": {"qudt_uri": "http://qudt.org/vocab/unit/M", "qudt_quantity_kind": "Length", "qudt_unit": "M"},
    "km": {"qudt_uri": "http://qudt.org/vocab/unit/KiloM", "qudt_quantity_kind": "Length", "qudt_unit": "KILOM"},
    "inch": {"qudt_uri": "http://qudt.org/vocab/unit/IN", "qudt_quantity_kind": "Length", "qudt_unit": "IN"},
    # velocity
    "km/h": {
        "qudt_uri": "http://qudt.org/vocab/unit/KiloM-PER-HR",
        "qudt_quantity_kind": "Velocity",
        "qudt_unit": "KILOM_PER_HR",
    },
    "m/s": {
        "qudt_uri": "http://qudt.org/vocab/unit/M-PER-SEC",
        "qudt_quantity_kind": "Velocity",
        "qudt_unit": "M_PER_SEC",
    },
    # acceleration
    "m/s^2": {
        "qudt_uri": "http://qudt.org/vocab/unit/M-PER-SEC2",
        "qudt_quantity_kind": "Acceleration",
        "qudt_unit": "M_PER_SEC2",
    },
    "cm/s^2": {
        "qudt_uri": "http://qudt.org/vocab/unit/CentiM-PER-SEC2",
        "qudt_quantity_kind": "Acceleration",
        "qudt_unit": "CENTIM_PER_SEC2",
    },
    # volume
    "ml": {"qudt_uri": "http://qudt.org/vocab/unit/MilliL", "qudt_quantity_kind": "Volume", "qudt_unit": "MILLIL"},
    "l": {"qudt_uri": "http://qudt.org/vocab/unit/L", "qudt_quantity_kind": "Volume", "qudt_unit": "L"},
    "cm^3": {"qudt_uri": "http://qudt.org/vocab/unit/CentiM3", "qudt_quantity_kind": "Volume", "qudt_unit": "CENTIM3"},
    # temperature
    "Celsius": {
        "qudt_uri": "http://qudt.org/vocab/unit/DEG_C",
        "qudt_quantity_kind": "Temperature",
        "qudt_unit": "DEG_C",
    },
    "Fahrenheit": {
        "qudt_uri": "http://qudt.org/vocab/unit/DEG_F",
        "qudt_quantity_kind": "Temperature",
        "qudt_unit": "DEG_F",
    },
    # angle
    "degrees": {"qudt_uri": "http://qudt.org/vocab/unit/Degree", "qudt_quantity_kind": "Angle", "qudt_unit": "DEG"},
    # angular speed
    "degrees/s": {
        "qudt_uri": "http://qudt.org/vocab/unit/DEG-PER-SEC",
        "qudt_quantity_kind": "AngularVelocity",
        "qudt_unit": "DEG_PER_SEC",
    },
    "rad/s": {
        "qudt_uri": "http://qudt.org/vocab/unit/RAD-PER-SEC",
        "qudt_quantity_kind": "AngularVelocity",
        "qudt_unit": "RAD_PER_SEC",
    },
    # power
    "W": {"qudt_uri": "http://qudt.org/vocab/unit/W", "qudt_quantity_kind": "Power", "qudt_unit": "W"},
    "kW": {"qudt_uri": "http://qudt.org/vocab/unit/KiloW", "qudt_quantity_kind": "Power", "qudt_unit": "KILOW"},
    "PS": {"qudt_uri": "http://qudt.org/vocab/unit/HP", "qudt_quantity_kind": "Power", "qudt_unit": "HP"},
    # energy / work
    "kWh": {"qudt_uri": "http://qudt.org/vocab/unit/KiloW-HR", "qudt_quantity_kind": "Energy", "qudt_unit": "KILOW_HR"},
    # mass
    "g": {"qudt_uri": "http://qudt.org/vocab/unit/GM", "qudt_quantity_kind": "Mass", "qudt_unit": "GM"},
    "kg": {"qudt_uri": "http://qudt.org/vocab/unit/KiloGM", "qudt_quantity_kind": "Mass", "qudt_unit": "KILOGM"},
    "lbs": {"qudt_uri": "http://qudt.org/vocab/unit/LB", "qudt_quantity_kind": "Mass", "qudt_unit": "LB"},
    # voltage
    "V": {"qudt_uri": "http://qudt.org/vocab/unit/V", "qudt_quantity_kind": "Voltage", "qudt_unit": "V"},
    # electric current
    "A": {"qudt_uri": "http://qudt.org/vocab/unit/A", "qudt_quantity_kind": "ElectricCurrent", "qudt_unit": "A"},
    # electric charge
    "Ah": {"qudt_uri": "http://qudt.org/vocab/unit/A_HR", "qudt_quantity_kind": "ElectricCharge", "qudt_unit": "A_HR"},
    # duration
    "ns": {"qudt_uri": "http://qudt.org/vocab/unit/NanoSEC", "qudt_quantity_kind": "Time", "qudt_unit": "NANOSEC"},
    "ms": {"qudt_uri": "http://qudt.org/vocab/unit/MilliSEC", "qudt_quantity_kind": "Time", "qudt_unit": "MILLISEC"},
    "s": {"qudt_uri": "http://qudt.org/vocab/unit/SEC", "qudt_quantity_kind": "Time", "qudt_unit": "SEC"},
    "min": {"qudt_uri": "http://qudt.org/vocab/unit/MIN", "qudt_quantity_kind": "Time", "qudt_unit": "MIN"},
    "h": {"qudt_uri": "http://qudt.org/vocab/unit/HR", "qudt_quantity_kind": "Time", "qudt_unit": "HR"},
    "day": {"qudt_uri": "http://qudt.org/vocab/unit/DAY", "qudt_quantity_kind": "Time", "qudt_unit": "DAY"},
    "weeks": {"qudt_uri": "http://qudt.org/vocab/unit/WK", "qudt_quantity_kind": "Time", "qudt_unit": "WK"},
    "months": {"qudt_uri": "http://qudt.org/vocab/unit/MO", "qudt_quantity_kind": "Time", "qudt_unit": "MO"},
    "years": {"qudt_uri": "http://qudt.org/vocab/unit/YR", "qudt_quantity_kind": "Time", "qudt_unit": "YR"},
    # pressure
    "mbar": {
        "qudt_uri": "http://qudt.org/vocab/unit/MilliBAR",
        "qudt_quantity_kind": "VaporPressure",
        "qudt_unit": "MILLIBAR",
    },
    "Pa": {"qudt_uri": "http://qudt.org/vocab/unit/PA", "qudt_quantity_kind": "VaporPressure", "qudt_unit": "PA"},
    "kPa": {
        "qudt_uri": "http://qudt.org/vocab/unit/KiloPA",
        "qudt_quantity_kind": "VaporPressure",
        "qudt_unit": "KILOPA",
    },
    "psi": {"qudt_uri": "http://qudt.org/vocab/unit/PSI", "qudt_quantity_kind": "VaporPressure", "qudt_unit": "PSI"},
    # mass flow rate
    "g/s": {
        "qudt_uri": "http://qudt.org/vocab/unit/GM-PER-SEC",
        "qudt_quantity_kind": "MassFlowRate",
        "qudt_unit": "GM_PER_SEC",
    },
    # mass per length
    "g/km": {
        "qudt_uri": "http://qudt.org/vocab/unit/GM-PER-KiloM",
        "qudt_quantity_kind": "MassPerLength",
        "qudt_unit": "GM_PER_KILOM",
    },
    # volume flow rate
    "l/h": {
        "qudt_uri": "http://qudt.org/vocab/unit/L-PER-HR",
        "qudt_quantity_kind": "VolumeFlowRate",
        "qudt_unit": "L_PER_HR",
    },
    # force
    "N": {"qudt_uri": "http://qudt.org/vocab/unit/N", "qudt_quantity_kind": "Force", "qudt_unit": "N"},
    "kN": {"qudt_uri": "http://qudt.org/vocab/unit/KiloN", "qudt_quantity_kind": "Force", "qudt_unit": "KILON"},
    # torque
    "Nm": {"qudt_uri": "http://qudt.org/vocab/unit/N-M", "qudt_quantity_kind": "Torque", "qudt_unit": "N_M"},
    # rotational speed
    "rpm": {
        "qudt_uri": "http://qudt.org/vocab/unit/REV-PER-MIN",
        "qudt_quantity_kind": "RotationalVelocity",
        "qudt_unit": "REV_PER_MIN",
    },
    # frequency
    "Hz": {"qudt_uri": "http://qudt.org/vocab/unit/HZ", "qudt_quantity_kind": "Frequency", "qudt_unit": "HZ"},
    "cpm": {"qudt_quantity_kind": "RotationalFrequency", "qudt_unit": "CYC_PER_MIN"},  # Custom (not present in QUDT)
    "bpm": {
        "qudt_uri": "http://qudt.org/vocab/unit/BEAT-PER-MIN",
        "qudt_quantity_kind": "HeartRate",
        "qudt_unit": "BEAT_PER_MIN",
    },
    # relation
    "ratio": {
        "qudt_uri": "http://qudt.org/vocab/unit/ONE-PER-ONE",
        "qudt_quantity_kind": "DimensionlessRatio",
        "qudt_unit": "ONE_PER_ONE",
    },
    "percent": {
        "qudt_uri": "http://qudt.org/vocab/unit/PERCENT",
        "qudt_quantity_kind": "DimensionlessRatio",
        "qudt_unit": "PERCENT",
    },
    "nm/km": {
        "qudt_quantity_kind": "DimensionlessRatio",
        "qudt_unit": "NANOM_PER_KILOM",
    },  # Custom (not present in QUDT)
    "dBm": {
        "qudt_uri": "http://qudt.org/vocab/unit/DeciB-MilliW",
        "qudt_quantity_kind": "Unknown",
        "qudt_unit": "DECIB_MILLIW",
    },
    "dB": {
        "qudt_uri": "http://qudt.org/vocab/unit/DeciB",
        "qudt_quantity_kind": "SoundPowerLevel",
        "qudt_unit": "DECIB",
    },
    # resistance
    "Ohm": {"qudt_uri": "http://qudt.org/vocab/unit/OHM", "qudt_quantity_kind": "Resistance", "qudt_unit": "OHM"},
    # iluminance
    "lx": {
        "qudt_uri": "http://qudt.org/vocab/unit/LUX",
        "qudt_quantity_kind": "LuminousFluxPerArea",
        "qudt_unit": "LUX",
    },
    # OTHERS
    # ------
    # rating
    "stars": {"qudt_quantity_kind": "Rating", "qudt_unit": "STARS"},  # Custom (not present in QUDT)
    # datetime
    "unix-time": {"qudt_quantity_kind": "DateTime", "qudt_unit": "UNIX_TIME"},  # Custom (not present in QUDT)
    "iso8601": {"qudt_quantity_kind": "DateTime", "qudt_unit": "ISO8601"},  # Custom (not present in QUDT)
    # energy-consumption-per-distance
    "kWh/km": {
        "qudt_quantity_kind": "EnergyPerDistance",
        "qudt_unit": "KILOW_HR_PER_100KILOM",
    },  # Custom (not present in QUDT)
    "Wh/km": {"qudt_quantity_kind": "EnergyPerDistance", "qudt_unit": "W_HR_PER_KILOM"},  # Custom (not present in QUDT)
    # volume-per-distance
    "ml/100km": {
        "qudt_quantity_kind": "VolumePerDistance",
        "qudt_unit": "MILLIL_PER_100KILOM",
    },  # Custom (not present in QUDT)
    "l/100km": {
        "qudt_quantity_kind": "VolumePerDistance",
        "qudt_unit": "L_PER_100KILOM",
    },  # Custom (not present in QUDT)
    # distance-per-volume
    "mpg-us": {
        "qudt_quantity_kind": "DistancePerVolume",
        "qudt_unit": "MILE_PER_GAL_US",
    },  # Custom (not present in QUDT)
    "mpg-uk": {
        "qudt_quantity_kind": "DistancePerVolume",
        "qudt_unit": "MILE_PER_GAL_UK",
    },  # Custom (not present in QUDT)
    "mpge": {
        "qudt_quantity_kind": "DistancePerVolume",
        "qudt_unit": "MILE_PER_GAL_US_EQ",
    },  # Custom (not present in QUDT)
    "mpg": {"qudt_quantity_kind": "DistancePerVolume", "qudt_unit": "MILE_PER_GAL"},  # Custom (not present in QUDT)
    "km/l": {"qudt_quantity_kind": "DistancePerVolume", "qudt_unit": "KILOM_PER_L"},  # Custom (not present in QUDT)
}
