# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pandas as pd
import pytest
from graphql import GraphQLDirective, GraphQLEnumType

import vss_tools.exporters.s2dm.type_builders as type_builders_module
from vss_tools.exporters.s2dm.predefined_elements import qudt_vocab
from vss_tools.exporters.s2dm.type_builders import _get_unit_args, create_unit_enums
from vss_tools.model import Qudt, VSSUnit

TEMPERATURE_QUANTITY_KIND_URI = "http://qudt.org/vocab/quantitykind/Temperature"
DEG_C_URI = "http://qudt.org/vocab/unit/DEG_C"


def _make_unit(key: str, quantity: str | None = None, qudt: Qudt | None = None) -> VSSUnit:
    return VSSUnit.model_construct(definition="test", unit=key, quantity=quantity, key=key, qudt=qudt)


class TestQudtVocabResolution:
    """resolve_qudt_unit_uri resolves native qudt: URIs against the vendored vocabulary."""

    def test_resolves_known_unit_uri(self):
        enum_type_name, enum_value_name = qudt_vocab.resolve_qudt_unit_uri(
            unit_uri=DEG_C_URI, quantity_kind_uri=TEMPERATURE_QUANTITY_KIND_URI, vss_key="celsius"
        )
        assert enum_type_name == "TemperatureUnit"
        assert enum_value_name == "DEG_C"

    def test_https_uris_fall_back_to_http(self):
        enum_type_name, enum_value_name = qudt_vocab.resolve_qudt_unit_uri(
            unit_uri="https://qudt.org/vocab/unit/DEG_C",
            quantity_kind_uri="https://qudt.org/vocab/quantitykind/Temperature",
            vss_key="celsius",
        )
        assert enum_type_name == "TemperatureUnit"
        assert enum_value_name == "DEG_C"

    def test_https_fallback_does_not_mask_unknown_uris(self):
        with pytest.raises(qudt_vocab.UnresolvedQudtUnitError):
            qudt_vocab.resolve_qudt_unit_uri(
                unit_uri=DEG_C_URI,
                quantity_kind_uri="https://qudt.org/vocab/quantitykind/Temperatur",
                vss_key="celsius",
            )

    def test_unresolved_unit_uri_raises_with_suggestions(self):
        with pytest.raises(qudt_vocab.UnresolvedQudtUnitError) as exc_info:
            qudt_vocab.resolve_qudt_unit_uri(
                unit_uri="http://qudt.org/vocab/unit/DEG_CC",
                quantity_kind_uri=TEMPERATURE_QUANTITY_KIND_URI,
                vss_key="bogus",
            )
        message = str(exc_info.value)
        assert "bogus" in message
        assert "DEG_C" in message  # closest match suggested

    def test_unit_not_in_quantity_kinds_enum_raises(self):
        # DEG_C is a real unit URI, but it isn't a value of the Length enum.
        with pytest.raises(qudt_vocab.UnresolvedQudtUnitError):
            qudt_vocab.resolve_qudt_unit_uri(
                unit_uri=DEG_C_URI,
                quantity_kind_uri="http://qudt.org/vocab/quantitykind/Length",
                vss_key="celsius",
            )

    def test_unresolved_quantity_kind_uri_raises_with_suggestions(self):
        with pytest.raises(qudt_vocab.UnresolvedQudtUnitError) as exc_info:
            qudt_vocab.resolve_qudt_unit_uri(
                unit_uri=DEG_C_URI,
                quantity_kind_uri="http://qudt.org/vocab/quantitykind/Temperatur",
                vss_key="celsius",
            )
        assert "Temperature" in str(exc_info.value)

    def test_get_enum_type_returns_full_vendored_value_set(self):
        enum_type = qudt_vocab.get_enum_type("TemperatureUnit")
        assert isinstance(enum_type, GraphQLEnumType)
        assert enum_type.name == "TemperatureUnit"
        # Vendored enum carries its full value set, not just VSS-used values.
        assert set(enum_type.values.keys()) >= {"DEG_C", "DEG_F", "K", "MEGAK", "MILLIK"}

    def test_get_enum_type_unknown_name_raises(self):
        with pytest.raises(qudt_vocab.UnresolvedQudtUnitError):
            qudt_vocab.get_enum_type("NotARealUnitEnum")

    def test_get_reference_directive(self):
        directive = qudt_vocab.get_reference_directive()
        assert isinstance(directive, GraphQLDirective)
        assert directive.name == "reference"


class TestNativeQudtBlockResolution:
    """type_builders._resolve_qudt/create_unit_enums use the vendored vocab for native qudt: blocks."""

    @pytest.fixture()
    def native_dynamic_units(self, monkeypatch):
        monkeypatch.setattr(
            type_builders_module,
            "dynamic_units",
            {
                "celsius": _make_unit(
                    "Celsius",
                    qudt=Qudt(unit=DEG_C_URI, **{"quantity-kind": TEMPERATURE_QUANTITY_KIND_URI}),
                ),
            },
        )

    def test_create_unit_enums_reuses_vendored_enum(self, native_dynamic_units):
        unit_enums, unit_metadata = create_unit_enums()
        assert "Temperature" in unit_enums
        enum_type = unit_enums["Temperature"]
        assert enum_type.name == "TemperatureUnit"
        # Full vendored value set is present, not trimmed to just "Celsius".
        assert "DEG_F" in enum_type.values
        assert unit_metadata["Temperature"]["qudt_backed"] is True

    def test_get_unit_args_uses_vendored_enum_value_name_as_default(self, native_dynamic_units):
        unit_enums, _ = create_unit_enums()
        leaf_row = pd.Series({"unit": "Celsius"})
        args = _get_unit_args(leaf_row, unit_enums)
        assert "unit" in args
        assert args["unit"].default_value == "DEG_C"

    @pytest.fixture()
    def bad_uri_dynamic_units(self, monkeypatch):
        monkeypatch.setattr(
            type_builders_module,
            "dynamic_units",
            {
                "bogus": _make_unit(
                    "Bogus",
                    qudt=Qudt(
                        unit="http://qudt.org/vocab/unit/NotReal", **{"quantity-kind": TEMPERATURE_QUANTITY_KIND_URI}
                    ),
                ),
            },
        )

    def test_unresolvable_native_uri_fails_export(self, bad_uri_dynamic_units):
        with pytest.raises(qudt_vocab.UnresolvedQudtUnitError):
            create_unit_enums()
