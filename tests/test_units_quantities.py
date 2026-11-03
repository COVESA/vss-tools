# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
"""
Tests for additive field-level merging of unit/quantity definitions redeclared
across multiple '-u'/'-q' files (see units_quantities.load_units_or_quantities).
"""

from pathlib import Path

import pytest

import vss_tools.model as model_module
from vss_tools.model import VSSUnit
from vss_tools.units_quantities import load_units


@pytest.fixture(autouse=True)
def _power_quantity(monkeypatch):
    """VSSUnit.quantity validation requires the quantity to be pre-registered."""
    monkeypatch.setattr(model_module, "dynamic_quantities", ["power"])


def _write(tmp_path: Path, name: str, content: str) -> Path:
    file = tmp_path / name
    file.write_text(content)
    return file


def test_later_file_adding_datatype_keeps_earlier_qudt_block(tmp_path):
    """A later file that only adds an allowed-datatype must not drop the earlier qudt: block."""
    first = _write(
        tmp_path,
        "units_first.yaml",
        """
kW:
  definition: Power measured in kilowatts
  unit: kilowatt
  quantity: power
  allowed-datatypes: ['numeric']
  qudt:
    unit: http://qudt.org/vocab/unit/KiloW
    quantity-kind: http://qudt.org/vocab/quantitykind/Power
""",
    )
    second = _write(
        tmp_path,
        "units_second.yaml",
        """
kW:
  definition: Power measured in kilowatts
  unit: kilowatt
  quantity: power
  allowed-datatypes: ["numeric", "string"]
""",
    )

    units = load_units([first, second])
    kw = units["kw"]
    assert isinstance(kw, VSSUnit)
    assert kw.allowed_datatypes == ["numeric", "string"]
    assert kw.qudt is not None
    assert kw.qudt.unit == "http://qudt.org/vocab/unit/KiloW"
    assert kw.qudt.kind == "http://qudt.org/vocab/quantitykind/Power"


def test_later_file_adding_qudt_block_is_kept(tmp_path):
    """A later file adding a qudt: block on top of an earlier bare definition is preserved."""
    first = _write(
        tmp_path,
        "units_first.yaml",
        """
kW:
  definition: Power measured in kilowatts
  unit: kilowatt
  quantity: power
  allowed-datatypes: ['numeric', 'string']
""",
    )
    second = _write(
        tmp_path,
        "units_second.yaml",
        """
kW:
  definition: Power measured in kilowatts
  unit: kilowatt
  quantity: power
  qudt:
    unit: http://qudt.org/vocab/unit/KiloW
    quantity-kind: http://qudt.org/vocab/quantitykind/Power
""",
    )

    units = load_units([first, second])
    kw = units["kw"]
    assert kw.allowed_datatypes == ["numeric", "string"]
    assert kw.qudt is not None
    assert kw.qudt.unit == "http://qudt.org/vocab/unit/KiloW"


def test_merge_logs_warning(tmp_path, caplog):
    first = _write(
        tmp_path,
        "units_first.yaml",
        """
kW:
  definition: Power measured in kilowatts
  unit: kilowatt
  quantity: power
  allowed-datatypes: ['numeric']
""",
    )
    second = _write(
        tmp_path,
        "units_second.yaml",
        """
kW:
  definition: Power measured in kilowatts
  unit: kilowatt
  quantity: power
  allowed-datatypes: ["numeric", "string"]
""",
    )

    load_units([first, second])
    assert "merging additional definition of 'kw'" in caplog.text
