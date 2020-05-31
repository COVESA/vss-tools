#!/usr/bin/python

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
    PASCAL = "pa"
    KILOPASCAL = "kpa"
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
    NETWONMETER = "N.m"
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
    INT8 = "Int8"
    UINT8 = "UInt8"
    INT16 = "Int16"
    UINT16 = "UInt16"
    INT32 = "Int32"
    UINT32 = "UInt32"
    INT64 = "Int64"
    UINT64 = "Int64"
    BOOLEAN = "Boolean"
    FLOAT = "Float"
    DOUBLE = "Double"
    STRING = "String"
    UNIX_TIMESTAMP = "UNIX Timestamp"

    @staticmethod
    def from_str(name):
        for vss_type in VSSDataType:
            if vss_type.value.lower() == name.lower():
                return vss_type
        raise Exception("Invalid VSS type %s only support %s" % (name, VSSDataType.values()))

    @staticmethod
    def values():
        return list(map(lambda v: v.value, VSSDataType))

