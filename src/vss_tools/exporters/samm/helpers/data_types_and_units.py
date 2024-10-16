# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from rdflib import XSD

from .namespaces import get_unit_uri

DataTypes = {
    "uint8": XSD.unsignedByte,
    "int8": XSD.byte,
    "uint16": XSD.unsignedShort,
    "int16": XSD.short,
    "uint32": XSD.unsignedInt,
    "int32": XSD.int,
    "uint64": XSD.unsignedLong,
    "int64": XSD.long,
    "boolean": XSD.boolean,
    "float": XSD.float,
    "double": XSD.double,
    "string": XSD.string,
    "dateTime": XSD.dateTime,
    "dateTimeStamp": XSD.dateTimeStamp,
    "iso8601": XSD.dateTimeStamp,
    "anyURI": XSD.anyURI,
}

DataUnits = {
    "cm3": get_unit_uri("cubicCentimetre"),
    "cm^3": get_unit_uri("cubicCentimetre"),
    "kw": get_unit_uri("kilowatt"),
    "kW": get_unit_uri("kilowatt"),
    "kWh": get_unit_uri("kilowattHour"),
    "l": get_unit_uri("litre"),
    "l/100km": get_unit_uri("litrePerHour"),
    "mm": get_unit_uri("millimetre"),
    "kg": get_unit_uri("kilogram"),
    "inch": get_unit_uri("inch"),
    "A": get_unit_uri("ampere"),
    "Ah": get_unit_uri("ampereHour"),
    "Nm": get_unit_uri("newtonMetre"),
    "N.m": get_unit_uri("newtonMetre"),
    "V": get_unit_uri("volt"),
    "celsius": get_unit_uri("degreeCelsius"),
    "cm/s": get_unit_uri("centimetrePerSecond"),
    "degree": get_unit_uri("degreeUnitOfAngle"),
    "degrees": get_unit_uri("degreeUnitOfAngle"),
    "degrees/s": get_unit_uri("degreePerSecond"),
    "g/s": get_unit_uri("gramPerSecond"),
    "kilometer": get_unit_uri("kilometre"),
    "km": get_unit_uri("kilometre"),
    "km/h": get_unit_uri("kilometrePerHour"),
    "kpa": get_unit_uri("kilopascal"),
    "kPa": get_unit_uri("kilopascal"),
    "l/h": get_unit_uri("litrePerHour"),
    "m": get_unit_uri("metre"),
    "m/s": get_unit_uri("metrePerSecond"),
    "m/s2": get_unit_uri("metrePerSecondSquared"),
    "m/s^2": get_unit_uri("metrePerSecondSquared"),
    "mbar": get_unit_uri("millibar"),
    "min": get_unit_uri("minuteUnitOfTime"),
    "ml": get_unit_uri("millilitre"),
    "pa": get_unit_uri("pascal"),
    "Pa": get_unit_uri("pascal"),
    "percent": get_unit_uri("percent"),
    "percentage": get_unit_uri("percent"),
    "ratio": get_unit_uri("rate"),
    "rpm": get_unit_uri("revolutionsPerMinute"),
    "g/km": get_unit_uri("kilogramPerKilometre"),
    "s": get_unit_uri("secondUnitOfTime"),
    "h": get_unit_uri("secondUnitOfTime"),
    "W": get_unit_uri("watt"),
    "cpm": get_unit_uri("cycle"),
    "bpm": get_unit_uri("cycle"),
    "iso8601": get_unit_uri("secondUnitOfTime"),
    "blank": get_unit_uri("blank"),
}
