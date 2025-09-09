# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""S2DM (Schema to Data Model) GraphQL exporter package."""

from .exporter import (
    cli,
    convert_to_graphql_field_name,
    convert_to_graphql_type_name,
    generate_s2dm_schema,
    get_metadata_df,
    print_schema_with_vspec_directives,
)

__all__ = [
    "cli",
    "convert_to_graphql_field_name", 
    "convert_to_graphql_type_name",
    "generate_s2dm_schema",
    "get_metadata_df",
    "print_schema_with_vspec_directives",
]
