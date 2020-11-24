#!/usr/bin/env python3

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

#
# Constant Types and Mappings
#

# noinspection PyPackageRequirements
from enum import Enum


class StringStyle(Enum):
    NONE = "none"
    CAMEL_CASE = "camelCase"
    CAMEL_BACK = "camelBack"
    CAPITAL_CASE = "capitalcase"
    CONST_CASE = "constcase"
    LOWER_CASE = "lowercase"
    PASCAL_CASE = "pascalcase"
    SENTENCE_CASE = "sentencecase"
    SNAKE_CASE = "snakecase"
    SPINAL_CASE = "spinalcase"
    TITLE_CASE = "titlecase"
    TRIM_CASE = "trimcase"
    UPPER_CASE = "uppercase"
    ALPHANUM_CASE = "alphanumcase"

    @staticmethod
    def from_str(name):
        for style in StringStyle:
            if style.value == name:
                return style
        raise Exception("Invalid String style %s only support %s" % (name, StringStyle.values()))

    @staticmethod
    def values():
        return list(map(lambda v: v.value, StringStyle))


class Unit(Enum):
    MILIMETER = "mm"
    CENTIMETER = "cm"
    METER = "m"
    KILOMETER = "km"
    KILOMETERPERHOUR = "km/h"
    METERSPERSECONDSQUARED = "m/s2"
    LITER = "l"
    DEGREECELCIUS = "celsius"
    DEGREE = "degrees"
    DEGREEPERSECOND = "degrees/s"
    KILOWATT = "kW"
    KILOWATTHOURS = "kWh"
    KILOGRAMM = "kg"
    VOLT = "V"
    AMPERE = "A"
    SECOND = "s"
    MINUTE = "min"
    WEEKS = "weeks"
    MONTHS = "months"
    UNIXTIMESTAMP = "UNIX Timestamp"
    PASCAL = "Pa"
    KILOPASCAL = "kPa"
    PERCENT = "percent"
    CUBICMETER = "cm3"
    HORSEPOWER = "PS"
    STARS = "stars"
    GRAMMPERSECOND = "g/s"
    GRAMMPERKM = "g/km"
    KILOWATTHOURSPER100KM = "kWh/100km"
    LITERPER100KM = "l/100km"
    LITERPERHOUR = "l/h"
    MILESPERGALLON = "mpg"
    POUND = "lbs"
    NEWTONMETER = "Nm"
    REVOLUTIONSPERMINUTE = "rpm"
    INCH = "inch"
    RATIO = "ratio"

    @staticmethod
    def from_str(name):
        for unit in Unit:
            if unit.value == name:
                return unit
        raise Exception("Invalid Unit %s only support %s" % (name, Unit.values()))

    @staticmethod
    def values():
        return list(map(lambda v: v.value, Unit))


class VSSType(Enum):
    BRANCH = "branch"
    RBRANCH = "rbranch"
    ATTRIBUTE = "attribute"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    ELEMENT = "element"

    @staticmethod
    def from_str(name):
        for vss_type in VSSType:
            if vss_type.value == name:
                return vss_type
        raise Exception("Invalid VSS data type %s only support %s" % (name, VSSType.values()))

    @staticmethod
    def values():
        return list(map(lambda v: v.value, VSSType))


class VSSDataType(Enum):
    INT8 = "int8"
    UINT8 = "uint8"
    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    INT64 = "int64"
    UINT64 = "uint64"
    BOOLEAN = "boolean"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "string"
    UNIX_TIMESTAMP = "UNIX Timestamp"
    INT8_ARRAY = "int8[]"
    UINT8_ARRAY = "uint8[]"
    INT16_ARRAY = "int16[]"
    UINT16_ARRAY = "uint16[]"
    INT32_ARRAY = "int32[]"
    UINT32_ARRAY = "uint32[]"
    INT64_ARRAY = "int64[]"
    UINT64_ARRAY = "uint64[]"
    BOOLEAN_ARRAY = "boolean[]"
    FLOAT_ARRAY = "float[]"
    DOUBLE_ARRAY = "double[]"
    STRING_ARRAY = "string[]"
    UNIX_TIMESTAMP_ARRAY = "UNIX Timestamp[]"

    @staticmethod
    def from_str(name):
        for vss_type in VSSDataType:
            if vss_type.value == name:
                return vss_type
        raise Exception("Invalid VSS datatype %s, valid types (case-sensitive) are %s" % (name, VSSDataType.values()))

    @staticmethod
    def values():
        return list(map(lambda v: v.value, VSSDataType))
