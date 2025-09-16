# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from vss_tools.utils.graphql_utils import (
    GraphQLElementType,
    convert_fqn_to_graphql_type_name,
    convert_name_for_graphql_schema,
    is_valid_graphql_name,
    sanitize_graphql_name,
)


class TestGraphQLNaming:
    """Test class for GraphQL naming utilities."""

    def test_convert_name_for_graphql_schema_types(self):
        """Test case conversion for GraphQL types."""
        assert convert_name_for_graphql_schema("simple", GraphQLElementType.TYPE) == "Simple"
        assert convert_name_for_graphql_schema("vehicle_body", GraphQLElementType.TYPE) == "VehicleBody"
        assert convert_name_for_graphql_schema("with-dash", GraphQLElementType.TYPE) == "WithDash"

    def test_convert_name_for_graphql_schema_fields(self):
        """Test case conversion for GraphQL fields."""
        assert convert_name_for_graphql_schema("simple", GraphQLElementType.FIELD) == "simple"
        assert convert_name_for_graphql_schema("SomeName", GraphQLElementType.FIELD) == "someName"
        assert convert_name_for_graphql_schema("with_underscore", GraphQLElementType.FIELD) == "withUnderscore"

    def test_convert_name_for_graphql_schema_enum_values(self):
        """Test case conversion for GraphQL enum values."""
        assert convert_name_for_graphql_schema("simple", GraphQLElementType.ENUM_VALUE) == "SIMPLE"
        assert (
            convert_name_for_graphql_schema("kilometer per hour", GraphQLElementType.ENUM_VALUE) == "KILOMETER_PER_HOUR"
        )
        assert convert_name_for_graphql_schema("with-dash", GraphQLElementType.ENUM_VALUE) == "WITH_DASH"

    def test_convert_name_for_graphql_schema_enum_with_prefix(self):
        """Test enum values starting with digits get underscore prefix."""
        assert convert_name_for_graphql_schema("123test", GraphQLElementType.ENUM_VALUE) == "_123TEST"

    def test_convert_name_for_graphql_schema_enums(self):
        """Test case conversion for GraphQL enums."""
        assert convert_name_for_graphql_schema("speed_unit", GraphQLElementType.ENUM) == "SpeedUnit"
        assert convert_name_for_graphql_schema("simple", GraphQLElementType.ENUM) == "Simple"

    def test_convert_fqn_to_graphql_type_name(self):
        """Test FQN to GraphQL type name conversion."""
        assert convert_fqn_to_graphql_type_name("Vehicle.Body.Lights") == "Vehicle_Body_Lights"
        assert convert_fqn_to_graphql_type_name("Vehicle.Body.Lights", "") == "VehicleBodyLights"
        assert convert_fqn_to_graphql_type_name("simple") == "Simple"

    def test_is_valid_graphql_name(self):
        """Test GraphQL name validation."""
        assert is_valid_graphql_name("ValidName") is True
        assert is_valid_graphql_name("_validName") is True
        assert is_valid_graphql_name("validName123") is True
        assert is_valid_graphql_name("123InvalidName") is False
        assert is_valid_graphql_name("invalid-name") is False
        assert is_valid_graphql_name("invalid name") is False

    def test_sanitize_graphql_name(self):
        """Test GraphQL name sanitization."""
        assert sanitize_graphql_name("valid_name", GraphQLElementType.TYPE) == "ValidName"
        assert sanitize_graphql_name("123invalid", GraphQLElementType.TYPE) == "_123invalid"
        assert sanitize_graphql_name("invalid@name$", GraphQLElementType.TYPE) == "InvalidName"
        assert sanitize_graphql_name("field with spaces", GraphQLElementType.FIELD) == "fieldWithSpaces"

    def test_python_keyword_handling(self):
        """Test that Python keywords are handled correctly."""
        # 'type' is not a Python keyword, 'class' is
        assert convert_name_for_graphql_schema("type", GraphQLElementType.TYPE) == "Type"
        assert convert_name_for_graphql_schema("class", GraphQLElementType.FIELD) == "class_"
