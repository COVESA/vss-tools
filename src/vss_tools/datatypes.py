# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from typing import Any, Callable, Set

from vss_tools import log

# Global objects to be extended by other code parts
dynamic_datatypes: Set[str] = set()
dynamic_quantities: list[str] = []
# This one contains the unit name as well as the list of allowed-datatypes
dynamic_units: dict[str, list] = {}


class DatatypesException(Exception):
    pass


def is_xintx(value: Any, signed: bool, bits: int):
    values = [value]
    if isinstance(value, list):
        values = value

    for v in values:
        if not isinstance(v, int):
            return False
        if not signed and v < 0:
            return False
        max = 2**bits - 1
        min = 0
        if signed:
            max = 2 ** (bits - 1) - 1
            min = -(2 ** (bits - 1))
        if not (v <= max and v >= min):
            return False
    return True


def is_uint8(value: Any) -> bool:
    return is_xintx(value, False, 8)


def is_int8(value: Any) -> bool:
    return is_xintx(value, True, 8)


def is_uint16(value: Any) -> bool:
    return is_xintx(value, False, 16)


def is_int16(value: Any) -> bool:
    return is_xintx(value, True, 16)


def is_uint32(value: Any) -> bool:
    return is_xintx(value, False, 32)


def is_int32(value: Any) -> bool:
    return is_xintx(value, True, 32)


def is_uint64(value: Any) -> bool:
    return is_xintx(value, False, 64)


def is_int64(value: Any) -> bool:
    return is_xintx(value, True, 64)


def is_x(value: Any, c: type) -> bool:
    values = [value]
    if isinstance(value, list):
        values = value
    return all([isinstance(v, c) for v in values])


def is_bool(value: Any) -> bool:
    return is_x(value, bool)


def is_float(value: Any) -> bool:
    return is_x(value, float) or is_x(value, int)


def is_string(value: Any) -> bool:
    return is_x(value, str)


def is_int(value: Any) -> bool:
    return is_x(value, int)


def is_numeric(value: Any) -> bool:
    return is_int(value) or is_float(value)


class Datatypes:
    # Types contain a tuple of the type name, the validation function whether
    # a value of type Any is a certain datatype
    # The last entry is a list of included subtypes
    # E.g. a unit8 is a valid uint16 usw..
    UINT8: tuple[str, Callable[[Any], bool], list[str]] = "uint8", is_uint8, []
    UINT8_ARRAY: tuple[str, Callable[[Any], bool], list[str]] = "uint8[]", is_uint8, []
    INT8: tuple[str, Callable[[Any], bool], list[str]] = "int8", is_int8, []
    INT8_ARRAY: tuple[str, Callable[[Any], bool], list[str]] = "int8[]", is_int8, []
    UINT16 = "uint16", is_uint16, ["uint8"]
    UINT16_ARRAY = "uint16[]", is_uint16, ["uint8[]"]
    INT16 = "int16", is_int16, ["int8"]
    INT16_ARRAY = "int16[]", is_int16, ["int8[]"]
    UINT32 = "uint32", is_uint32, ["uint16", "uint8"]
    UINT32_ARRAY = "uint32[]", is_uint32, ["uint16[]", "uint8[]"]
    INT32 = "int32", is_int32, ["int16", "int8"]
    INT32_ARRAY = "int32[]", is_int32, ["int16[]", "int8[]"]
    UINT64 = "uint64", is_uint64, ["uint32", "uint16", "uint8"]
    UINT64_ARRAY = "uint64[]", is_uint64, ["uint32[]", "uint16[]", "uint8[]"]
    INT64 = "int64", is_int64, ["int32", "int16", "int8"]
    INT64_ARRAY = "int64[]", is_int64, ["int32[]", "int16[]", "int8[]"]
    BOOLEAN: tuple[str, Callable[[Any], bool], list[str]] = "boolean", is_bool, []
    BOOLEAN_ARRAY: tuple[str, Callable[[Any], bool], list[str]] = (
        "boolean[]",
        is_bool,
        [],
    )
    FLOAT: tuple[str, Callable[[Any], bool], list[str]] = "float", is_float, []
    FLOAT_ARRAY: tuple[str, Callable[[Any], bool], list[str]] = "float[]", is_float, []
    DOUBLE: tuple[str, Callable[[Any], bool], list[str]] = "double", is_float, []
    DOUBLE_ARRAY: tuple[str, Callable[[Any], bool], list[str]] = (
        "double[]",
        is_float,
        [],
    )
    STRING: tuple[str, Callable[[Any], bool], list[str]] = "string", is_string, []
    STRING_ARRAY: tuple[str, Callable[[Any], bool], list[str]] = (
        "string[]",
        is_string,
        [],
    )
    NUMERIC = (
        "numeric",
        is_numeric,
        [
            "int64",
            "int32",
            "int16",
            "int8",
            "uint64",
            "uint32",
            "uint16",
            "uint8",
            "float",
            "double",
        ],
    )
    NUMERIC_ARRAY = (
        "numeric[]",
        is_numeric,
        [
            "int64[]",
            "int32[]",
            "int16[]",
            "int8[]",
            "uint64[]",
            "uint32[]",
            "uint16[]",
            "uint8[]",
            "float[]",
            "double[]",
        ],
    )
    types = [
        UINT8,
        UINT8_ARRAY,
        INT8,
        INT8_ARRAY,
        UINT16,
        UINT16_ARRAY,
        INT16,
        INT16_ARRAY,
        UINT32,
        UINT32_ARRAY,
        INT32,
        INT32_ARRAY,
        UINT64,
        UINT64_ARRAY,
        INT64,
        INT64_ARRAY,
        BOOLEAN,
        BOOLEAN_ARRAY,
        FLOAT,
        FLOAT_ARRAY,
        DOUBLE,
        DOUBLE_ARRAY,
        STRING,
        STRING_ARRAY,
        NUMERIC,
        NUMERIC_ARRAY,
    ]

    @classmethod
    def get_type(cls, datatype: str) -> tuple[str, Callable, list[str]] | None:
        for t in cls.types:
            if datatype == t[0]:
                return t
        return None

    @classmethod
    def is_datatype(cls, value: Any, datatype: str) -> bool:
        t = cls.get_type(datatype)
        if t is None:
            raise DatatypesException(f"Unsupported datatype: {datatype}")
        return t[1](value)

    @classmethod
    def is_subtype_of(cls, check: str, base: str) -> bool:
        check_type = cls.get_type(check)
        if not check_type:
            raise DatatypesException(f"Not a valid type: '{check}'")
        base_type = cls.get_type(base)
        if not base_type:
            raise DatatypesException(f"Not a valid type: '{base}'")
        return check in base_type[2] or check == base


def get_fqn_namespaced_datatypes(fqn: str | None = None) -> dict[str, str]:
    """
    We want to be able to reference datatypes from within the same file
    or same namespace since we support structs in structs

    For instance if we have the struct Types.A.B.C
    and we have another struct Types.A.B.D then the D struct
    should be able to reference C as a datatype
    """
    if not fqn:
        return {}
    fqn_namespaced_datatypes = {}
    for t in dynamic_datatypes:
        # This excludes referencing the own struct as a datatype
        if fqn.startswith(t):
            continue

        # fqn: Types.A.B.C.x_property
        # t: Types.A.B.D
        # We are checking whether fqn starts with Types.A.B
        # in this case we add {D: Types.A.B.D}
        if fqn.startswith(".".join(t.split(".")[:-1])):
            fqn_namespaced_datatypes[(t.split(".")[-1])] = t

    if fqn_namespaced_datatypes:
        log.debug(f"Namespaced datatypes, {fqn=}, {fqn_namespaced_datatypes=}")
    return fqn_namespaced_datatypes


def get_dynamic_datatypes(fqn: str | None = None) -> list[str]:
    """
    Aggregator to gather all custom datatypes for a given fqn
    The fqn is needed to support the namespaced custom datatypes
    """
    fqn_namespaced_datatypes = set(get_fqn_namespaced_datatypes(fqn).keys())
    dynamic_array_datatypes = [f"{t}[]" for t in dynamic_datatypes | fqn_namespaced_datatypes]
    return list(dynamic_datatypes) + dynamic_array_datatypes + list(fqn_namespaced_datatypes)


def get_all_datatypes(fqn: str | None = None) -> list[str]:
    static_datatypes = [t[0] for t in Datatypes.types]
    dynamic_datatypes = get_dynamic_datatypes(fqn)
    return static_datatypes + dynamic_datatypes


def resolve_datatype(datatype: str, fqn: str | None) -> str:
    """
    Resolves a possible shortened namespaced type into the
    fully qualified types
    """
    if not fqn:
        return datatype

    array = is_array(datatype)
    datatype = datatype.rstrip("[]")

    resvoled = get_fqn_namespaced_datatypes(fqn).get(datatype, datatype)
    if array:
        resvoled += "[]"
    return resvoled


def is_array(datatype: str) -> bool:
    return datatype.endswith("[]")
