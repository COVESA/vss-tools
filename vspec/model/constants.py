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
from enum import Enum, EnumMeta
from typing import Sequence, Type, TypeVar


T = TypeVar("T")


class EnumMetaWithReverseLookup(EnumMeta):
    """This class extends EnumMeta and adds:
     - from_str(str): reverse lookup
     - values(): sequence of values
    """
    def __new__(typ, *args, **kwargs):
        cls = super().__new__(typ, *args, **kwargs)
        if not hasattr(cls, "__reverse_lookup__"):
            cls.__reverse_lookup__ = {
                v.value: v for v in cls.__members__.values()
            }
        if not hasattr(cls, "__values__"):
            cls.__values__ = tuple(v.value for v in cls.__members__.values())
        return cls

    def from_str(cls: Type[T], value: str) -> T:
        return cls.__reverse_lookup__[value]

    def values(cls: Type[T]) -> Sequence[str]:
        return cls.__values__


class StringStyle(Enum, metaclass=EnumMetaWithReverseLookup):
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


class Unit(Enum, metaclass=EnumMetaWithReverseLookup):
    MILIMETER = "mm"
    CENTIMETER = "cm"
    METER = "m"
    KILOMETER = "km"
    KILOMETERPERHOUR = "km/h"
    METERSPERSECONDSQUARED = "m/s^2"
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
    CUBICMETER = "cm^3"
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


class VSSType(Enum, metaclass=EnumMetaWithReverseLookup):
    BRANCH = "branch"
    RBRANCH = "rbranch"
    ATTRIBUTE = "attribute"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    ELEMENT = "element"


class VSSDataType(Enum, metaclass=EnumMetaWithReverseLookup):
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
