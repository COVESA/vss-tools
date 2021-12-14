# (C) 2021 BMW Group - All rights reserved.
# AUTHOR: Daniel Wilms BMW Group

from enum import Enum
from rdflib import XSD, URIRef

class VssoConcepts (Enum):
    
    EMPTY =             ""
    BELONGS_TO =        "belongsToVehicleComponent"
    HOLDS_VALUE =       "holdsState"
    HAS_SIGNAL =        "hasDynamicVehicleProperty"
    HAS_ATTRIBUTE =     "hasStaticVehicleProperty"
    PART_OF_VEHICLE =   "partOfVehicle"
    PART_OF_VEH_COMP =  "partOfVehicleComponent"
    HAS_COMP_INST =     "hasInstance"
    HAS_ENUM_VALUE =    "hasEnumerationValue"
    HAS_ENUM_DEF =      "hasDefaultEnumerationValue"
    DATA_TYPE =         "vehiclePropertyDatatype"
    BASE_DATA_TYPE =    "baseDatatype"
    UNIT =              "unit"
    MIN =               "minValue"
    MAX =               "maxValue"
    RES =               "resolution"
    VEHICLE =           "Vehicle"
    VEHICLE_SIGNAL =    "ObservableVehicleProperty"
    VEHICLE_ACT =       "ActuatableVehicleProperty"
    VEHICLE_COMP =      "VehicleComponent"
    VEHICLE_PROP =      "VehicleProperty"
    VEHICLE_PROP_DYN =  "DynamicVehicleProperty"
    VEHICLE_PROP_STAT = "StaticVehicleProperty"
    VEHICLE_PROP_NUM =  "NumericVehicleProperty"
    VEHICLE_PROP_ENUM = "EnumeratedVehicleProperty"
    ENUM_VALUE =        "EnumerationValue"
    ARRAY_TYPE =        "ArrayType"
    VEHICLE_PROP_NAME=  "vehiclePropertyName"
    VEHICLE_COMP_NAME=  "vehicleComponentName"
    ENUM_NAME =         "enumerationName"
    ENUM_DESC =         "enumerationDescription"


    def __init__ (self, vsso_name):
        self.ns = "https://github.com/danielwilms/vsso-demo/"
        self.vsso_name = vsso_name

    @property
    def uri(self):
        return URIRef(f'{self.ns}{self.value}')

    @property
    def uri_string(self):
        return f'{self.ns}{self.value}'



DataTypes = {'uint8': XSD.unsignedByte,
    'int8': XSD.byte,
    'uint16': XSD.unsignedShort,
    'int16': XSD.short,
    'uint32': XSD.unsignedInt,
    'int32': XSD.int,
    'uint64': XSD.unsignedLong,
    'int64': XSD.long,
    'boolean': XSD.boolean,
    'float': XSD.float,
    'double': XSD.double,
    'string': XSD.string
}
    
Namespaces = {
    'unit': "http://purl.oclc.org/NET/ssnx/qu/unit#",
    'cdt': "http://w3id.org/lindt/custom_datatypes#"
}

DataUnits = {
    'A': URIRef(Namespaces["unit"] + "ampere"),
    'celsius': URIRef(Namespaces["unit"] + "degreeCelsius"),
    'cm/s': URIRef(Namespaces["unit"] + "centimetrePerSecond"),
    'cm^3': URIRef(Namespaces["unit"] + "cubicCentimetre"),
    'cm3': URIRef(Namespaces["unit"] + "cubicCentimetre"),
    'degree': URIRef(Namespaces["unit"] + "degreeUnitOfAngle"),
    'degrees': URIRef(Namespaces["unit"] + "degreeUnitOfAngle"),
    'degrees/s': URIRef(Namespaces["unit"] + "degreePerSecond"),
    'g/km': URIRef(Namespaces["unit"] + "gramPerKilometre"),  # Not available in qu-rec20
    'g/s': URIRef(Namespaces["unit"] + "gramPerSecond"),
    'inch': URIRef(Namespaces["unit"] + "inch"),
    'kg': URIRef(Namespaces["unit"] + "kilogram"),
    'kilometer': URIRef(Namespaces["unit"] + "kilometre"),
    'km/h': URIRef(Namespaces["unit"] + "kilometrePerHour"),
    'km': URIRef(Namespaces["unit"] + "kilometre"),
    'kpa': URIRef(Namespaces["unit"] + "kilopascal"),
    'kPa': URIRef(Namespaces["unit"] + "kilopascal"),
    'kw': URIRef(Namespaces["unit"] + "kilowatt"),
    'kW': URIRef(Namespaces["unit"] + "kilowatt"),
    'kWh': URIRef(Namespaces["unit"] + "kilowattHour"),
    'l/100km': URIRef(Namespaces["unit"] + "litrePerHundredKilometre"),  # Not available in qu-rec20
    'l/h': URIRef(Namespaces["unit"] + "litrePerHour"),  # Not available in qu-rec20
    'l': URIRef(Namespaces["unit"] + "litre"),
    'm/s': URIRef(Namespaces["unit"] + "metrePerSecond"),
    'm/s^2': URIRef(Namespaces["unit"] + "metrePerSecondSquared"),
    'm/s2': URIRef(Namespaces["unit"] + "metrePerSecondSquared"),
    'm': URIRef(Namespaces["unit"] + "metre"),
    'mbar': URIRef(Namespaces["unit"] + "millibar"),
    'min': URIRef(Namespaces["unit"] + "minuteUnitOfTime"),
    'ml': URIRef(Namespaces["unit"] + "millilitre"),
    'mm': URIRef(Namespaces["unit"] + "millimetre"),
    'N.m': URIRef(Namespaces["unit"] + "newtonMetre"),
    'Nm': URIRef(Namespaces["unit"] + "newtonMetre"),
    'pa': URIRef(Namespaces["unit"] + "pascal"),
    'Pa': URIRef(Namespaces["unit"] + "pascal"),
    'percent': URIRef(Namespaces["unit"] + "percent"),
    'percentage': URIRef(Namespaces["unit"] + "percent"),
    'ratio': URIRef(Namespaces["unit"] + "ratio"),
    'rpm': URIRef(Namespaces["unit"] + "revolutionPerMinute"),  # Not available in qu-rec20
    's': URIRef(Namespaces["unit"] + "secondUnitOfTime"),
    'V': URIRef(Namespaces["unit"] + "volt")
}
