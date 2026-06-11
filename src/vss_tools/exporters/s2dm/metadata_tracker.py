# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Metadata tracking for S2DM GraphQL directives."""

from __future__ import annotations

from typing import Any


def init_vspec_comments() -> dict[str, dict[str, Any]]:
    """
    Initialize dictionary for storing VSS metadata for directives.

    Structure:
    - vss_types: type_name -> {"element": "BRANCH"|"STRUCT", "fqn": "..."}
    - field_vss_types: field_path -> {"element": "ATTRIBUTE"|"SENSOR"|"ACTUATOR"|"STRUCT_PROPERTY", "fqn": "..."}
    - field_ranges: field_path -> {"min": value, "max": value} for @range directive
    - field_deprecated: field_path -> "deprecation reason" for @deprecated directive
    - instance_tags: tag_name -> {"element": "BRANCH", "fqn": "...", "instances": "..."}
    - instance_tag_types: type_name -> tag_name

    Returns:
        Initialized metadata tracking dictionary
    """
    return {
        "instance_tags": {},
        "instance_tag_types": {},
        "vss_types": {},
        "field_vss_types": {},
        "field_ranges": {},
        "field_deprecated": {},
    }


def build_field_path(type_name: str, field_name: str) -> str:
    """
    Build a field path from type name and field name.

    Args:
        type_name: GraphQL type name
        field_name: GraphQL field name

    Returns:
        Field path in format "TypeName.fieldName"
    """
    return f"{type_name}.{field_name}"
