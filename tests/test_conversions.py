# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import sys

from caseconverter import DELIMITERS, pascalcase

sys.path.insert(0, "src")

from vss_tools.utils.graphql_utils import DEFAULT_CONVERSIONS, GraphQLElementType, convert_name_for_graphql_schema
from vss_tools.utils.string_conversion_utils import handle_fqn_conversion

print("=== Creating S2DM conversions in same scope ===")

# Create S2DM conversions in the same scope
S2DM_CONVERSIONS = DEFAULT_CONVERSIONS.copy()
S2DM_CONVERSIONS.update(
    {
        GraphQLElementType.TYPE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
        GraphQLElementType.INTERFACE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
        GraphQLElementType.UNION: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
        GraphQLElementType.INPUT: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
    }
)

print("DEFAULT_CONVERSIONS keys:", len(DEFAULT_CONVERSIONS))
print("S2DM_CONVERSIONS keys:", len(S2DM_CONVERSIONS))
print("FIELD in DEFAULT:", GraphQLElementType.FIELD in DEFAULT_CONVERSIONS)
print("FIELD in S2DM:", GraphQLElementType.FIELD in S2DM_CONVERSIONS)

# Test the conversion
test_cases = ["with.dots", "Vehicle.Body.Lights"]

print("\n=== Testing conversions ===")
for case in test_cases:
    field_default = convert_name_for_graphql_schema(case, GraphQLElementType.FIELD, DEFAULT_CONVERSIONS)
    type_default = convert_name_for_graphql_schema(case, GraphQLElementType.TYPE, DEFAULT_CONVERSIONS)

    field_s2dm = convert_name_for_graphql_schema(case, GraphQLElementType.FIELD, S2DM_CONVERSIONS)
    type_s2dm = convert_name_for_graphql_schema(case, GraphQLElementType.TYPE, S2DM_CONVERSIONS)

    print(f"{case}:")
    print(f"  DEFAULT field: {field_default}, type: {type_default}")
    print(f"  S2DM    field: {field_s2dm}, type: {type_s2dm}")
