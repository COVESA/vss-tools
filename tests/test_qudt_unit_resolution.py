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
from vss_tools.exporters.s2dm.type_builders import _get_unit_args, create_unit_enums
from vss_tools.model import VSSUnit


def _make_unit(key: str, quantity: str) -> VSSUnit:
    """Build a minimal VSSUnit for testing without triggering quantity validation."""
    return VSSUnit.model_construct(definition="test", unit=key, quantity=quantity, key=key)


def _leaf(unit: str) -> pd.Series:
    return pd.Series({"unit": unit})


class TestUnitAliasResolution:
    """Tests for QUDT_ALIASES backward-compatibility in unit enum building and _get_unit_args.

    Two scenarios are covered:
    - Current model: units.yaml registers the new canonical names ("day", "Celsius").
    - Legacy model: units.yaml still registers the old names ("days", "celsius") and
      the vspec also still uses those old names.
    """

    @pytest.fixture()
    def current_dynamic_units(self, monkeypatch):
        """Simulate a current model whose units.yaml uses the new canonical names."""
        monkeypatch.setattr(
            type_builders_module,
            "dynamic_units",
            {
                "day": _make_unit("day", "time"),
                "Celsius": _make_unit("Celsius", "temperature"),
            },
        )

    @pytest.fixture()
    def legacy_dynamic_units(self, monkeypatch):
        """Simulate a legacy model whose units.yaml still uses the old names."""
        monkeypatch.setattr(
            type_builders_module,
            "dynamic_units",
            {
                "days": _make_unit("days", "time"),
                "celsius": _make_unit("celsius", "temperature"),
            },
        )

    def test_canonical_day_resolves(self, current_dynamic_units):
        """Current models using 'day' produce a TimeUnit enum and a unit argument."""
        unit_enums, _ = create_unit_enums()
        assert "Time" in unit_enums, "TimeUnit enum should be built from 'day'"
        args = _get_unit_args(_leaf("day"), unit_enums)
        assert "unit" in args
        assert args["unit"].default_value == "day"

    def test_canonical_celsius_resolves(self, current_dynamic_units):
        """Current models using 'Celsius' produce a TemperatureUnit enum and a unit argument."""
        unit_enums, _ = create_unit_enums()
        assert "Temperature" in unit_enums, "TemperatureUnit enum should be built from 'Celsius'"
        args = _get_unit_args(_leaf("Celsius"), unit_enums)
        assert "unit" in args
        assert args["unit"].default_value == "Celsius"

    def test_alias_days_resolves(self, legacy_dynamic_units):
        """Legacy models with 'days' in units.yaml and vspec still get a TimeUnit enum and unit argument."""
        unit_enums, _ = create_unit_enums()
        assert "Time" in unit_enums, "TimeUnit enum should be built even when dynamic_units has 'days'"
        args = _get_unit_args(_leaf("days"), unit_enums)
        assert "unit" in args, "'days' should resolve via alias and produce a unit argument"

    def test_alias_celsius_resolves(self, legacy_dynamic_units):
        """Legacy models with 'celsius' in units.yaml and vspec still get a TemperatureUnit enum and unit argument."""
        unit_enums, _ = create_unit_enums()
        assert "Temperature" in unit_enums, "TemperatureUnit enum should be built even when dynamic_units has 'celsius'"
        args = _get_unit_args(_leaf("celsius"), unit_enums)
        assert "unit" in args, "'celsius' should resolve via alias and produce a unit argument"
