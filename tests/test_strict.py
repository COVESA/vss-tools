# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import tempfile
from pathlib import Path

import pydantic
import pytest
import yaml
from vss_tools.strict import StrictException, StrictExceptions, StrictOption, load_strict_exceptions


class TestStrictException:
    def test_init_with_fqn_only(self):
        exception = StrictException(fqn="Vehicle.Speed")
        assert exception.fqn == "Vehicle.Speed"
        assert exception.options is None

    def test_init_with_options(self):
        options = {StrictOption.NAME_STYLE}
        exception = StrictException(fqn="Vehicle.Speed", options=options)
        assert exception.fqn == "Vehicle.Speed"
        assert exception.options == options

    def test_init_with_multiple_options(self):
        options = {StrictOption.NAME_STYLE, StrictOption.UNKNOWN_ATTRIBUTE}
        exception = StrictException(fqn="Vehicle.Speed", options=options)
        assert exception.fqn == "Vehicle.Speed"
        assert exception.options == options


class TestLoadStrictExceptions:
    def test_load_with_none_file(self):
        exceptions = load_strict_exceptions(None)
        assert isinstance(exceptions, StrictExceptions)
        assert len(exceptions.names) == 0
        assert len(exceptions.attributes) == 0

    def test_load_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump({}, f)
            temp_path = Path(f.name)
            exceptions = load_strict_exceptions(temp_path)
            assert isinstance(exceptions, StrictExceptions)
            assert len(exceptions.names) == 0
            assert len(exceptions.attributes) == 0

    def test_load_with_name_style_exception(self):
        data = {"Vehicle.Speed": ["name-style"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            exceptions = load_strict_exceptions(temp_path)
            assert "Vehicle.Speed" in exceptions.names
            assert "Vehicle.Speed" not in exceptions.attributes

    def test_load_with_unknown_attribute_exception(self):
        data = {"Vehicle.Speed": ["unknown-attribute"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            exceptions = load_strict_exceptions(temp_path)
            assert "Vehicle.Speed" not in exceptions.names
            assert "Vehicle.Speed" in exceptions.attributes

    def test_load_with_multiple_exceptions(self):
        data = {"Vehicle.Speed": ["name-style", "unknown-attribute"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            exceptions = load_strict_exceptions(temp_path)
            assert "Vehicle.Speed" in exceptions.names
            assert "Vehicle.Speed" in exceptions.attributes

    def test_load_with_null_options(self):
        data = {"Vehicle.Speed": None}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            exceptions = load_strict_exceptions(temp_path)
            assert "Vehicle.Speed" in exceptions.names
            assert "Vehicle.Speed" in exceptions.attributes

    def test_load_multiple_entries(self):
        data = {
            "Vehicle.Speed": ["name-style"],
            "Vehicle.Engine.RPM": ["unknown-attribute"],
            "Vehicle.Body.Doors": None,
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            exceptions = load_strict_exceptions(temp_path)
            assert "Vehicle.Speed" in exceptions.names
            assert "Vehicle.Speed" not in exceptions.attributes
            assert "Vehicle.Engine.RPM" not in exceptions.names
            assert "Vehicle.Engine.RPM" in exceptions.attributes
            assert "Vehicle.Body.Doors" in exceptions.names
            assert "Vehicle.Body.Doors" in exceptions.attributes

    def test_load_invalid_entry(self):
        data = {
            "Vehicle.Speed": ["what am I"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            with pytest.raises(pydantic.ValidationError):
                _ = load_strict_exceptions(temp_path)

    def test_load_with_invalid_file_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            _ = f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)
            with pytest.raises(ValueError):
                _ = load_strict_exceptions(temp_path)

    def test_load_with_non_dict_content(self):
        data = ["not", "a", "dict"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            with pytest.raises(ValueError, match="Invalid exceptions file format"):
                _ = load_strict_exceptions(temp_path)

    def test_load_with_nonexistent_file(self):
        nonexistent_path = Path("/nonexistent/file.yaml")
        with pytest.raises(FileNotFoundError):
            _ = load_strict_exceptions(nonexistent_path)

    def test_load_with_empty_string_options(self):
        data: dict[str, list[str] | None] = {"Vehicle.Speed": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            yaml.dump(data, f)
            temp_path = Path(f.name)
            exceptions = load_strict_exceptions(temp_path)
            assert "Vehicle.Speed" in exceptions.names
            assert "Vehicle.Speed" in exceptions.attributes
