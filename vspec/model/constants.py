#!/usr/bin/env python3

# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Constant Types and Mappings
#
# noinspection PyPackageRequirements
from __future__ import annotations
import re
import logging
import sys
from collections import abc
from collections.abc import Sequence
from enum import Enum, EnumMeta
from typing import TextIO, TypeVar

import yaml

NON_ALPHANUMERIC_WORD = re.compile("[^A-Za-z0-9]+")

NON_ALPHANUMERIC_WORD = re.compile('[^A-Za-z0-9]+')

T = TypeVar("T")


class VSSUnit(str):
    """String subclass for storing unit information."""

    id: str  # Typically abbreviation like "V"
    unit: str | None = None  # Typically full name like "Volt"
    definition: str | None = None
    quantity: str | None = None  # Typically quantity, like "Voltage"
    allowed_datatypes: list[str] | None = None  # Typically quantity, like "Voltage"

    def __new__(
        cls,
        id: str,
        unit: str | None = None,
        definition: str | None = None,
        quantity: str | None = None,
        allowed_datatypes: list[str] | None = None,
    ) -> VSSUnit:
        self = super().__new__(cls, id)
        self.id = id
        self.unit = unit
        self.definition = definition
        self.quantity = quantity
        self.allowed_datatypes = allowed_datatypes
        return self

    @property
    def value(self):
        return self


class VSSQuantity(str):
    """String subclass for storing quantity information."""

    id: str  # Identifier preferably taken from a standard, like ISO 80000
    definition: str  # Explanation of quantity, for example reference to standard
    remark: str | None = None  # remark as defined in for example ISO 80000
    comment: str | None = None

    def __new__(
        cls,
        id: str,
        definition: str,
        remark: str | None = None,
        comment: str | None = None,
    ) -> VSSQuantity:
        self = super().__new__(cls, id)
        self.id = id
        self.definition = definition
        self.remark = remark
        self.comment = comment
        return self

    @property
    def value(self):
        return self


class EnumMetaWithReverseLookup(EnumMeta):
    """This class extends EnumMeta and adds:
    - from_str(str): reverse lookup
    - values(): sequence of values
    """

    def __new__(typ, *args, **kwargs):
        cls = super().__new__(typ, *args, **kwargs)
        if not hasattr(cls, "__reverse_lookup__"):
            cls.__reverse_lookup__ = {v.value: v for v in cls.__members__.values()}
        if not hasattr(cls, "__values__"):
            cls.__values__ = tuple(v.value for v in cls.__members__.values())
        return cls

    def from_str(cls: type[T], value: str) -> T:
        return cls.__reverse_lookup__[value]  # type: ignore[attr-defined]

    def values(cls: type[T]) -> Sequence[str]:
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

    @classmethod
    def is_numeric(cls, datatype):
        """
        Return true if this datatype accepts numerical values
        """
        if datatype in [
            VSSDataType.STRING,
            VSSDataType.STRING_ARRAY,
            VSSDataType.BOOLEAN,
            VSSDataType.BOOLEAN_ARRAY,
        ]:
            return False
        return True


class VSSUnitCollection:
    units: dict[str, VSSUnit] = dict()

    @staticmethod
    def get_config_dict(yaml_file: TextIO, key: str) -> dict[str, dict[str, str]]:
        yaml_config = yaml.safe_load(yaml_file)
        if (len(yaml_config) == 1) and (key in yaml_config):
            # Old style unit file
            configs = yaml_config.get(key, {})
        else:
            # New style unit file
            configs = yaml_config
        return configs

    @classmethod
    def reset_units(cls):
        cls.units = dict()

    @classmethod
    def load_config_file(cls, config_file: str) -> int:
        added_configs = 0
        with open(config_file) as my_yaml_file:
            my_units = cls.get_config_dict(my_yaml_file, "units")
            added_configs = len(my_units)
            for k, v in my_units.items():
                unit = k
                if "unit" in v:
                    unit = v["unit"]
                elif "label" in v:
                    # Old syntax
                    unit = v["label"]
                definition = None
                if "definition" in v:
                    definition = v["definition"]
                elif "description" in v:
                    # Old syntax
                    definition = v["description"]

                quantity = None
                if "quantity" in v:
                    quantity = v["quantity"]
                elif "domain" in v:
                    # Old syntax
                    quantity = v["domain"]
                else:
                    logging.error("No quantity (domain) found for unit %s", k)
                    sys.exit(-1)

                if (VSSQuantityCollection.nbr_quantities() > 0) and (
                    VSSQuantityCollection.get_quantity(quantity) is None
                ):
                    # Only give info on first occurance and only if quantities exist at all
                    logging.info(
                        "Quantity %s used by unit %s has not been defined", quantity, k
                    )
                    VSSQuantityCollection.add_quantity(quantity)

                allowed_datatypes = None

                if "allowed_datatypes" in v:
                    allowed_datatypes = []
                    for datatype in v["allowed_datatypes"]:
                        allowed_datatypes.append(datatype)
                        if datatype == "numeric":
                            # Symbolic type for all numeric types
                            continue
                        try:
                            VSSDataType.from_str(datatype)
                        except KeyError:
                            logging.error(
                                "Unknown datatype %s in unit definition", datatype
                            )
                            sys.exit(-1)

                unit_node = VSSUnit(k, unit, definition, quantity, allowed_datatypes)
                if k in cls.units:
                    logging.warning("Redefinition of unit %s", k)
                cls.units[k] = unit_node
        return added_configs

    @classmethod
    def get_unit(cls, id: str) -> VSSUnit | None:
        if id in cls.units:
            return cls.units[id]
        else:
            return None


class VSSQuantityCollection:
    quantities: dict[str, VSSQuantity] = dict()

    @classmethod
    def reset_quantities(cls):
        cls.quantities = dict()

    @classmethod
    def load_config_file(cls, config_file: str) -> int:
        added_quantities = 0
        with open(config_file) as my_yaml_file:
            my_quantities = yaml.safe_load(my_yaml_file)
            added_quantities = len(my_quantities)
            for k, v in my_quantities.items():
                if isinstance(v, abc.Mapping) and "definition" in v:
                    definition = v["definition"]
                else:
                    logging.error("No definition found for quantity %s", k)
                    sys.exit(-1)
                remark = None
                if "remark" in v:
                    remark = v["remark"]
                comment = None
                if "comment" in v:
                    comment = v["comment"]

                quantity_node = VSSQuantity(k, definition, remark, comment)
                if k in cls.quantities:
                    logging.warning("Redefinition of quantity %s", k)
                cls.quantities[k] = quantity_node
        return added_quantities

    @classmethod
    def get_quantity(cls, id: str) -> VSSQuantity | None:
        if id in cls.quantities:
            return cls.quantities[id]
        else:
            return None

    @classmethod
    def nbr_quantities(cls) -> int:
        return len(cls.quantities)

    @classmethod
    def add_quantity(cls, id: str) -> None:
        if id not in cls.quantities:
            quantity_node = VSSQuantity(id, "Automatically generated quantity")
            cls.quantities[id] = quantity_node


class VSSTreeType(Enum, metaclass=EnumMetaWithReverseLookup):
    SIGNAL_TREE = "signal_tree"
    DATA_TYPE_TREE = "data_type_tree"

    def available_types(self):
        if self.value == "signal_tree":
            available_types = {"branch", "sensor", "actuator", "attribute"}
        else:
            available_types = {"branch", "struct", "property"}

        return available_types
