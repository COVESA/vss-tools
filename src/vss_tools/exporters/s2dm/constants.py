# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Constants and configurations for S2DM exporter."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from caseconverter import DELIMITERS, pascalcase

from vss_tools.utils.graphql_utils import (
    DEFAULT_CONVERSIONS,
    GraphQLElementType,
    load_predefined_schema_elements,
)
from vss_tools.utils.string_conversion_utils import handle_fqn_conversion

# VSS leaf types to track in field metadata (corresponds to VspecElement enum in directives.graphql)
# Note: BRANCH is excluded as it's handled separately for object types
VSS_LEAF_TYPES = ["SENSOR", "ACTUATOR", "ATTRIBUTE"]


def get_s2dm_conversions() -> Dict[GraphQLElementType, Callable[[str], str]]:
    """
    Configure GraphQL naming conversions for S2DM schema generation.

    Overrides default conversions for type-like elements to handle fully qualified names
    (e.g., Vehicle.Body -> Vehicle_Body) by excluding dots from delimiters.

    Returns:
        Dictionary mapping GraphQL element types to conversion functions
    """
    s2dm_conversions = DEFAULT_CONVERSIONS.copy()
    s2dm_conversions.update(
        {
            # Override type-like elements to handle FQNs (Vehicle.Body -> Vehicle_Body)
            # Use standard delimiters (space, dash, underscore) but NOT dots for FQN names
            GraphQLElementType.TYPE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.INTERFACE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.UNION: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.INPUT: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.ENUM: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
        }
    )
    return s2dm_conversions


# S2DM-specific conversions
S2DM_CONVERSIONS = get_s2dm_conversions()

# Load custom directives from predefined GraphQL schema files
_, CUSTOM_DIRECTIVES = load_predefined_schema_elements(Path(__file__).parent / "predefined_elements")

# Custom directives loaded from SDL
VSpecDirective = CUSTOM_DIRECTIVES["vspec"]
RangeDirective = CUSTOM_DIRECTIVES["range"]
InstanceTagDirective = CUSTOM_DIRECTIVES["instanceTag"]


class S2DMExporterException(Exception):
    """Exception raised for errors in the S2DM export process."""

    pass
