# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for s2dm/type_builders.py pure functions.

These tests exercise individual functions without needing to run the full CLI,
so regressions surface immediately at the function level rather than only when
a real VSS tree is processed.
"""

from pathlib import Path

import pytest
from graphql import GraphQLObjectType, GraphQLString, print_schema

from vss_tools.exporters.s2dm.type_builders import (
    _clean_enum_name,
    _parse_instances_simple,
    create_unit_enums,
    resolve_datatype_to_graphql,
)
from vss_tools.exporters.s2dm import generate_s2dm_schema
from vss_tools.main import get_trees
from vss_tools.utils.graphql_scalars import VSS_DATATYPE_MAP


HERE = Path(__file__).parent
TEST_UNITS = HERE / "vspec" / "test_s2dm" / "test_units.yaml"
TEST_QUANT = HERE / "vspec" / "test_s2dm" / "test_quantities.yaml"
MIXED_CASE_VSPEC = HERE / "vspec" / "test_s2dm" / "test_mixed_case_unit.vspec"
SEAT_VSPEC = HERE / "vspec" / "test_s2dm" / "example_seat.vspec"


def _load_s2dm(vspec: Path) -> str:
    """Helper: load vspec and return printed SDL."""
    tree, _ = get_trees(
        vspec=vspec,
        include_dirs=(),
        aborts=(),
        strict=False,
        extended_attributes=(),
        quantities=(TEST_QUANT,),
        units=(TEST_UNITS,),
        overlays=(),
        expand=False,
    )
    schema, _, _, _ = generate_s2dm_schema(tree)
    return print_schema(schema)


class TestCleanEnumName:
    """_clean_enum_name converts arbitrary strings to valid GraphQL enum member names."""

    def test_plain_string_unchanged(self):
        assert _clean_enum_name("PARK") == "PARK"

    def test_digit_prefix_gets_underscore(self):
        assert _clean_enum_name("1") == "_1"
        assert _clean_enum_name("42") == "_42"

    def test_decimal_dot_replaced(self):
        assert _clean_enum_name("2.5") == "_2_DOT_5"
        assert _clean_enum_name("1.0") == "_1_DOT_0"

    def test_dash_replaced(self):
        assert _clean_enum_name("some-value") == "some_DASH_value"

    def test_combined_transformations(self):
        # Starts with digit AND contains dot
        assert _clean_enum_name("3.14") == "_3_DOT_14"

    def test_negative_number(self):
        # Leading minus is not a digit, so no underscore prefix — dash is replaced
        assert _clean_enum_name("-100") == "_DASH_100"

    def test_string_starting_with_letter_unchanged(self):
        assert _clean_enum_name("DRIVE") == "DRIVE"
        assert _clean_enum_name("NEUTRAL") == "NEUTRAL"


class TestParseInstancesSimple:
    """_parse_instances_simple converts VSS instance declarations to dimension arrays."""

    def test_simple_string_list_wrapped_in_single_dimension(self):
        result = _parse_instances_simple(["Left", "Right"])
        assert result == [["Left", "Right"]]

    def test_expand_pattern_row(self):
        result = _parse_instances_simple(["Row[1,2]"])
        assert result == [["Row1", "Row2"]]

    def test_mixed_expand_and_list(self):
        # VSS seat: ["Row[1,2]", ["DriverSide", "PassengerSide"]]
        result = _parse_instances_simple(["Row[1,2]", ["DriverSide", "PassengerSide"]])
        assert result == [["Row1", "Row2"], ["DriverSide", "PassengerSide"]]

    def test_plain_list_is_single_dimension(self):
        result = _parse_instances_simple(["A", "B", "C"])
        assert result == [["A", "B", "C"]]

    def test_single_item_list(self):
        result = _parse_instances_simple(["OnlyOne"])
        assert result == [["OnlyOne"]]

    def test_nested_list_only(self):
        result = _parse_instances_simple([["X", "Y"]])
        assert result == [["X", "Y"]]


class TestResolveDatatype:
    """resolve_datatype_to_graphql maps VSS datatype strings to GraphQL types."""

    def test_primitive_types_map_correctly(self):
        for vss_type, gql_type in VSS_DATATYPE_MAP.items():
            if not vss_type.endswith("[]"):
                result = resolve_datatype_to_graphql(vss_type, {})
                assert result == gql_type, f"Failed for {vss_type}"

    def test_array_type_wraps_in_list(self):
        from graphql import GraphQLList, GraphQLNonNull

        result = resolve_datatype_to_graphql("uint8[]", {})
        assert isinstance(result, GraphQLList)

    def test_unknown_type_falls_back_to_string(self):
        result = resolve_datatype_to_graphql("unknown_datatype_xyz", {})
        assert result == GraphQLString

    def test_custom_struct_type_resolved_from_registry(self):
        mock_struct = GraphQLObjectType("MyStruct", {})
        registry = {"MyStruct": mock_struct}
        result = resolve_datatype_to_graphql("MyStruct", registry)
        assert result is mock_struct

    def test_array_of_custom_struct_resolved(self):
        from graphql import GraphQLList

        mock_struct = GraphQLObjectType("MyStruct", {})
        registry = {"MyStruct": mock_struct}
        result = resolve_datatype_to_graphql("MyStruct[]", registry)
        assert isinstance(result, GraphQLList)

    def test_unknown_struct_array_falls_back_to_string_list(self):
        from graphql import GraphQLList

        result = resolve_datatype_to_graphql("NoSuchStruct[]", {})
        assert isinstance(result, GraphQLList)


class TestCreateUnitEnums:
    """create_unit_enums builds GraphQL enum types from the loaded dynamic_units registry."""

    def test_enums_created_for_loaded_quantities(self):
        # Load test units so dynamic_units is populated
        get_trees(
            vspec=SEAT_VSPEC,
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(TEST_QUANT,),
            units=(TEST_UNITS,),
            overlays=(),
            expand=False,
        )
        unit_enums, unit_metadata = create_unit_enums()

        assert "length" in unit_enums
        assert "angle" in unit_enums
        assert "relation" in unit_enums

    def test_enum_type_names_are_pascal_cased_with_suffix(self):
        get_trees(
            vspec=SEAT_VSPEC,
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(TEST_QUANT,),
            units=(TEST_UNITS,),
            overlays=(),
            expand=False,
        )
        unit_enums, _ = create_unit_enums()
        assert unit_enums["length"].name == "LengthUnitEnum"
        assert unit_enums["angle"].name == "AngleUnitEnum"

    def test_new_quantities_generate_enums(self):
        """angular_velocity and power quantities added to test fixtures generate enums."""
        get_trees(
            vspec=MIXED_CASE_VSPEC,
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(TEST_QUANT,),
            units=(TEST_UNITS,),
            overlays=(),
            expand=False,
        )
        unit_enums, _ = create_unit_enums()
        assert "angular_velocity" in unit_enums
        assert "power" in unit_enums
        assert unit_enums["angular_velocity"].name == "AngularVelocityUnitEnum"
        assert unit_enums["power"].name == "PowerUnitEnum"


class TestUnitCaseSensitivityRegression:
    """Regression tests for the bug introduced by #523 and fixed by #535.

    After #523 made dynamic_units use lowercase keys, the validator started returning
    unit_data.key (original YAML casing, e.g. "W" for Watt) rather than the lowercase
    dict key. _get_unit_args then looked up dynamic_units[unit] where unit="W" — KeyError.
    The fix is dynamic_units[unit.lower()].
    """

    def test_lowercase_unit_key_generates_schema(self):
        """rpm (lowercase YAML key) produces AngularVelocityUnitEnum without error."""
        sdl = _load_s2dm(MIXED_CASE_VSPEC)
        assert "AngularVelocityUnitEnum" in sdl

    def test_uppercase_unit_key_generates_schema(self):
        """W (uppercase YAML key) produces PowerUnitEnum without KeyError — regression for #535."""
        sdl = _load_s2dm(MIXED_CASE_VSPEC)
        assert "PowerUnitEnum" in sdl

    def test_uppercase_unit_field_has_unit_argument(self):
        """Fields using an uppercase-keyed unit get a unit argument in the schema."""
        sdl = _load_s2dm(MIXED_CASE_VSPEC)
        assert "unit: PowerUnitEnum" in sdl

    def test_lowercase_unit_field_has_unit_argument(self):
        sdl = _load_s2dm(MIXED_CASE_VSPEC)
        assert "unit: AngularVelocityUnitEnum" in sdl

    def test_enum_value_names_are_uppercase(self):
        """Unit display names are converted to UPPERCASE for GraphQL enum member names."""
        sdl = _load_s2dm(MIXED_CASE_VSPEC)
        assert "WATT" in sdl
        assert "REVOLUTION_PER_MINUTE" in sdl or "REVOLUTION" in sdl


class TestAllowedValueEdgeCases:
    """Edge cases in _clean_enum_name for allowed-value enum generation."""

    def test_float_allowed_values_with_dot(self):
        # 2.5 → _2_DOT_5
        assert _clean_enum_name("2.5") == "_2_DOT_5"

    def test_negative_integer_allowed_value(self):
        # -1 → _DASH_1 (leading dash, not digit)
        result = _clean_enum_name("-1")
        assert result.startswith("_DASH_") or result == "_DASH_1"

    def test_zero_allowed_value(self):
        assert _clean_enum_name("0") == "_0"

    def test_string_with_no_transformation_needed(self):
        assert _clean_enum_name("ACTIVE") == "ACTIVE"
        assert _clean_enum_name("REVERSE") == "REVERSE"
