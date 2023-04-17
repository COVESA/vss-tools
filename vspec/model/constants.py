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
import re
from enum import Enum, EnumMeta
from typing import (
    Sequence, Type, TypeVar, Optional, Dict, Tuple, Iterator, TextIO
)

import yaml


NON_ALPHANUMERIC_WORD = re.compile('[^A-Za-z0-9]+')

T = TypeVar("T")


class VSSConstant(str):
    """String subclass that can tag it with description and domain.
    """
    label: str
    description: Optional[str] = None
    domain: Optional[str] = None

    def __new__(cls, label: str, value: str, description: str = "", domain: str = "") -> 'VSSConstant':
        self = super().__new__(cls, value)
        self.label = label
        self.description = description
        self.domain = domain
        return self

    @property
    def value(self):
        return self


def dict_to_constant_config(name: str, info: Dict[str, str]) -> Tuple[str, VSSConstant]:
    label = info['label']
    label = NON_ALPHANUMERIC_WORD.sub('', label).upper()
    description = info.get('description', '')
    domain = info.get('domain', '')
    return label, VSSConstant(info['label'], name, description, domain)


def iterate_config_members(config: Dict[str, Dict[str, str]]) -> Iterator[Tuple[str, VSSConstant]]:
    for u, v in config.items():
        yield dict_to_constant_config(u, v)


class VSSRepositoryMeta(type):
    """This class defines the enumeration behavior for vss:
     - Access through Class.ATTRIBUTE
     - Class.add_config(Dict[str, Dict[str, str]]): Adds values from file
     - from_str(str): reverse lookup
     - values(): sequence of values
    """

    def __new__(mcs, cls, bases, classdict):
        cls = super().__new__(mcs, cls, bases, classdict)

        if not hasattr(cls, '__reverse_lookup__'):
            cls.__reverse_lookup__ = {
                v.value: v for v in cls.__members__.values()
            }
        if not hasattr(cls, '__values__'):
            cls.__values__ = list(cls.__reverse_lookup__.keys())

        return cls

    def __getattr__(cls, key: str) -> str:
        try:
            return cls.__members__[key]  # type: ignore[index]
        except KeyError as e:
            raise AttributeError(
                f"type object '{cls.__name__}' has no attribute '{key}'"
            ) from e

    def add_config(cls, config: Dict[str, Dict[str, str]]):
        for k, v in iterate_config_members(config):
            if v.value not in cls.__reverse_lookup__ and k not in cls.__members__:
                cls.__members__[k] = v  # type: ignore[index]
                cls.__reverse_lookup__[v.value] = v  # type: ignore[index]
                cls.__values__.append(v.value)  # type: ignore[attr-defined]

    def from_str(cls: Type[T], value: str) -> T:
        return cls.__reverse_lookup__[value]  # type: ignore[attr-defined]

    def values(cls: Type[T]) -> Sequence[str]:
        return cls.__values__  # type: ignore[attr-defined]


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
        return cls.__reverse_lookup__[value]  # type: ignore[attr-defined]

    def values(cls: Type[T]) -> Sequence[str]:
        return cls.__values__  # type: ignore[attr-defined]


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


class VSSType(Enum, metaclass=EnumMetaWithReverseLookup):
    BRANCH = "branch"
    ATTRIBUTE = "attribute"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    STRUCT = "struct"
    PROPERTY = "property"


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


class Unit(metaclass=VSSRepositoryMeta):
    __members__: Dict[str, str] = dict()

    @staticmethod
    def get_config_dict(yaml_file: TextIO, key: str) -> Dict[str, Dict[str, str]]:
        yaml_config = yaml.safe_load(yaml_file)
        configs = yaml_config.get(key, {})
        return configs

    @staticmethod
    def load_config_file(config_file: str) -> int:
        added_configs = 0
        with open(config_file) as my_yaml_file:
            my_units = Unit.get_config_dict(my_yaml_file, 'units')
            added_configs = len(my_units)
            Unit.add_config(my_units)
        return added_configs


class VSSTreeType(Enum, metaclass=EnumMetaWithReverseLookup):
    SIGNAL_TREE = "signal_tree"
    DATA_TYPE_TREE = "data_type_tree"

    def available_types(self):
        if self.value == "signal_tree":
            available_types = set(["branch", "sensor", "actuator", "attribute"])
        else:
            available_types = set(["branch", "struct", "property"])

        return available_types
