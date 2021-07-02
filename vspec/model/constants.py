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

__all__ = (
    "StringStyle",
    "Unit",
    "VSSType",
    "VSSDataType",
)


T = TypeVar("T")


class VSSConstant(str):
    """String subclass that can tag it with description and domain.
    """
    __slots__ = ("description", "domain")

    def __new__(
        cls,
        value: str,
        description: str = "",
        domain: str = "",
    ) -> None:
        self = super().__new__(cls, value)
        self.description = description
        self.domain = domain
        return self


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
    """Data Unit Types

    A signal can optionally specify a unit of measurement from the
    following set. This list composed with definition according to
    International Units (SI) and few automotive specific units:
    [Specification](https://www.iso.org/standard/30669.html),
    [Wikipedia](https://en.wikipedia.org/wiki/International_System_of_Units)
    """
    MILIMETER = VSSConstant("mm", "Millimeter", "Distance")
    CENTIMETER = VSSConstant("cm", "Centimeter", "Distance")
    METER = VSSConstant("m", "Meter", "Distance")
    KILOMETER = VSSConstant("km", "Kilometer", "Distance")
    KILOMETERPERHOUR = VSSConstant("km/h", "Kilometers per hour", "Speed")
    METERSPERSECONDSQUARED = VSSConstant(
        "m/s^2",
        "Acceleration in meters per second squared",
        "Acceleration"
    )
    LITER = VSSConstant("l", "Liter", "Volume")
    DEGREECELCIUS = VSSConstant("celsius", "Degrees Celsius", "Temperature")
    DEGREE = VSSConstant("degrees", "Angle in degrees", "Angle")
    DEGREEPERSECOND = VSSConstant(
        "degrees/s",
        "Angular speed in degrees/s",
        "Angular Speed"
    )
    KILOWATT = VSSConstant("kW", "Kilowatt", "Power")
    KILOWATTHOURS = VSSConstant("kWh", "Kilowatt hours", "Power")
    KILOGRAMM = VSSConstant("kg", "Kilograms", "Weight")
    VOLT = VSSConstant("V", "Potential difference in volt", "Electrical")
    AMPERE = VSSConstant("A", "Current in amperes", "Electrical")
    SECOND = VSSConstant("s", "Seconds", "Time")
    MINUTE = VSSConstant("min", "Minutes", "Time")
    WEEKS = VSSConstant("weeks", "Weeks", "Time")
    MONTHS = VSSConstant("months", "Months", "Time")
    UNIXTIMESTAMP = VSSConstant(
        "UNIX Timestamp",
        "Seconds since January 1st 1970 UTC",
        "Time"
    )
    PASCAL = VSSConstant("Pa", "Pascal",  "Pressure")
    KILOPASCAL = VSSConstant("kPa", "Kilo-Pascal", "Pressure")
    PERCENT = VSSConstant("percent", "Percent", "Relation")
    CUBICCENTIMETER = VSSConstant("cm^3", "Cubic Centimetres", "Volume")
    HORSEPOWER = VSSConstant("PS", "Horsepower", "Power")
    STARS = VSSConstant("stars", "?", "?")
    GRAMMPERSECOND = VSSConstant("g/s", "Grams per second", "?")
    GRAMMPERKM = VSSConstant("g/km", "Grams per Kilometer", "?")
    KILOWATTHOURSPER100KM = VSSConstant(
        "kWh/100km",
        "Kilowatt hours per 100 Kilometers",
        "?"
    )
    LITERPER100KM = VSSConstant("l/100km", "Liters per 100 Kilometers", "?")
    LITERPERHOUR = VSSConstant("l/h", "Liters per hour", "?")
    MILESPERGALLON = VSSConstant("mpg", "Miles per gallon", "?")
    POUND = VSSConstant("lbs", "Pound", "Weight")
    NEWTONMETER = VSSConstant("Nm", "Torque", "Force")
    REVOLUTIONSPERMINUTE = VSSConstant(
        "rpm",
        "Rotations per minute",
        "Frequency"
    )
    INCH = VSSConstant("inch", "Inches", "Distance")
    RATIO = VSSConstant("ratio",  "Ratio", "Relation")

class VSSType(Enum, metaclass=EnumMetaWithReverseLookup):
    """Node Types

    https://genivi.github.io/vehicle_signal_specification/rule_set/data_entry/
    https://genivi.github.io/vehicle_signal_specification/rule_set/branches/
    """
    BRANCH = "branch"
    RBRANCH = "rbranch"
    ATTRIBUTE = "attribute"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    ELEMENT = "element"


class VSSDataType(Enum, metaclass=EnumMetaWithReverseLookup):
    """Data Types

    Each
    [data entry](https://genivi.github.io/vehicle_signal_specification/rule_set/data_entry)
    specifies a `datatype` from the following set (from FrancaIDL).
    Datatypes shall not be used in
    [branch entry](https://genivi.github.io/vehicle_signal_specification/rule_set/branches)
    """
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
