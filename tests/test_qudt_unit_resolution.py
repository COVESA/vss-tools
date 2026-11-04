# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pandas as pd
import pytest

import vss_tools.exporters.s2dm.type_builders as type_builders_module
from vss_tools.exporters.s2dm.graphql_directive_processor import GraphQLDirectiveProcessor
from vss_tools.exporters.s2dm.type_builders import _get_unit_args, create_unit_enums
from vss_tools.model import VSSUnit


def _make_unit(key: str, quantity: str, definition: str = "test") -> VSSUnit:
    """Build a minimal VSSUnit without a qudt block, without triggering quantity validation."""
    return VSSUnit.model_construct(definition=definition, unit=key, quantity=quantity, key=key, qudt=None)


class TestCustomUnitEnums:
    """Units without a `qudt:` block are grouped by VSS quantity into `Custom<Quantity>Unit` enums."""

    @pytest.fixture()
    def custom_dynamic_units(self, monkeypatch):
        # Keys are lowercase like dynamic_units; the original casing lives in VSSUnit.key.
        stars = _make_unit("stars", "rating", "Rating in stars")
        monkeypatch.setattr(
            type_builders_module,
            "dynamic_units",
            {
                "stars": stars,
                "star rating": stars,  # dynamic_units also registers the unit's descriptive text
                "kwh/100km": _make_unit("kWh/100km", "energy-consumption-per-distance"),
                "wh/km": _make_unit("Wh/km", "energy-consumption-per-distance"),
            },
        )

    def test_custom_enum_per_quantity_with_only_declared_units(self, custom_dynamic_units):
        unit_enums, unit_metadata = create_unit_enums()
        assert set(unit_enums) == {"CustomRating", "CustomEnergyConsumptionPerDistance"}
        assert unit_enums["CustomRating"].name == "CustomRatingUnit"
        assert list(unit_enums["CustomRating"].values) == ["STARS"]
        assert len(unit_enums["CustomEnergyConsumptionPerDistance"].values) == 2
        assert unit_metadata["CustomRating"]["qudt_backed"] is False

    def test_custom_value_carries_vss_definition(self, custom_dynamic_units):
        unit_enums, _ = create_unit_enums()
        assert unit_enums["CustomRating"].values["STARS"].description == "Rating in stars"

    def test_unit_argument_defaults_to_custom_value(self, custom_dynamic_units):
        unit_enums, _ = create_unit_enums()
        args = _get_unit_args(pd.Series({"unit": "stars"}), unit_enums)
        assert args["unit"].type is unit_enums["CustomRating"]
        assert args["unit"].default_value == "STARS"

    def test_custom_enum_directives_use_vspec_only(self, custom_dynamic_units):
        unit_enums, metadata = create_unit_enums()
        lines = [
            "enum CustomRatingUnit {",
            '  """Rating in stars"""',
            "  STARS",
            "}",
        ]
        result = GraphQLDirectiveProcessor()._process_unit_enum_directives(lines, metadata, set())
        assert result[0] == 'enum CustomRatingUnit @vspec(element: QUANTITY_KIND, originalName: "rating") {'
        assert result[2] == '  STARS @vspec(element: UNIT, originalName: "stars")'
        assert not any("@reference" in line for line in result)
