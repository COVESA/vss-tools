# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
GraphQL scalar types and datatype mappings for VSS exporters.

This module provides reusable GraphQL scalar type definitions and mappings
that can be used across different VSS exporters. It centralizes the 
custom scalar types needed for VSS data types.
"""

from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLInt,
    GraphQLScalarType,
    GraphQLString,
)

from vss_tools.datatypes import Datatypes

# Custom scalar types for VSS data types
VSS_SCALARS = {
    "Int8": GraphQLScalarType(name="Int8"),
    "UInt8": GraphQLScalarType(name="UInt8"),
    "Int16": GraphQLScalarType(name="Int16"),
    "UInt16": GraphQLScalarType(name="UInt16"),
    "UInt32": GraphQLScalarType(name="UInt32"),
    "Int64": GraphQLScalarType(name="Int64"),
    "UInt64": GraphQLScalarType(name="UInt64"),
}

# Mapping from VSS datatypes to GraphQL types
VSS_DATATYPE_MAP = {
    Datatypes.INT8[0]: VSS_SCALARS["Int8"],
    Datatypes.UINT8[0]: VSS_SCALARS["UInt8"],
    Datatypes.INT16[0]: VSS_SCALARS["Int16"],
    Datatypes.UINT16[0]: VSS_SCALARS["UInt16"],
    Datatypes.INT32[0]: GraphQLInt,
    Datatypes.UINT32[0]: VSS_SCALARS["UInt32"],
    Datatypes.INT64[0]: VSS_SCALARS["Int64"],
    Datatypes.UINT64[0]: VSS_SCALARS["UInt64"],
    Datatypes.FLOAT[0]: GraphQLFloat,
    Datatypes.DOUBLE[0]: GraphQLFloat,
    Datatypes.BOOLEAN[0]: GraphQLBoolean,
    Datatypes.STRING[0]: GraphQLString,
}

def get_vss_scalar_types() -> list[GraphQLScalarType]:
    """Get list of all VSS custom scalar types for schema inclusion."""
    return list(VSS_SCALARS.values())
