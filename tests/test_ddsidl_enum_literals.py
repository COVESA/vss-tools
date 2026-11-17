# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import re
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from vss_tools.exporters import ddsidl


def _key(literal: str) -> str:
    return literal.removeprefix("_").lower()


def _export(values: list[str], tmp_path: Path, monkeypatch, datatype: str = "string") -> tuple[str, list[str]]:
    source = tmp_path / "test.vspec"
    target = tmp_path / "out.idl"
    source.write_text(
        yaml.safe_dump(
            {
                "A": {"type": "branch", "description": "Root"},
                "A.Signal": {
                    "type": "attribute",
                    "datatype": datatype,
                    "description": "Signal",
                    "allowed": values,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ddsidl, "idl_file_buffer", [])
    result = CliRunner().invoke(ddsidl.cli, ["-s", str(source), "-o", str(target)])
    assert result.exit_code == 0, result.output
    output = target.read_text(encoding="utf-8")
    match = re.search(r"enum (\S+)\{([^}]+)\};", output)
    assert match is not None, output
    return match.group(1), match.group(2).split(",")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("NO_BLANK", "NO_BLANK"),
        ("WITH_ BLANK", "WITH__BLANK"),
        ("123", "d123"),
        ("d123", "d123"),
        ("_module", "_module"),
        ("_Legacy", "_Legacy"),
        ("A1_b2", "A1_b2"),
        ("vss_c3b6", "vss_c3b6"),
    ],
)
def test_preserves_existing_valid_literals(value: str, expected: str):
    assert ddsidl.get_allowed_enum_literal(value) == expected


@pytest.mark.parametrize(
    "value",
    ["SMÖRGÅSTÅRTA", "ö", "温度", "🚗", "", "A-B", "a.b", "a/b", "a:b", "\t", "__name", "_", "\ud800", "\ud83d\ude97"],
)
def test_arbitrary_strings_become_ascii_identifiers(value: str):
    literal = ddsidl.get_allowed_enum_literal(value)
    assert re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", literal.removeprefix("_"))


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ö", "vss_c3b6"),
        ("SMÖRGÅSTÅRTA", "vss_534dc3965247c3855354c385525441"),
        ("温度", "vss_e6b8a9e5baa6"),
        ("🚗", "vss_f09f9a97"),
        ("", "vss_"),
        ("A-B", "vss_412d42"),
        ("\ud800", "vss_eda080"),
        ("\ud83d\ude97", "vss_eda0bdedba97"),
    ],
)
def test_encoded_spelling_is_stable(value: str, expected: str):
    assert ddsidl.get_allowed_enum_literal(value) == expected


@pytest.mark.parametrize("value", ["module", "MoDuLe", "enum", "TRUE", "false", "Object", "ValueBase"])
def test_unescaped_keywords_are_not_emitted(value: str):
    literal = ddsidl.get_allowed_enum_literal(value)
    assert literal.startswith("_") or literal.lower() != value.lower()


@pytest.mark.parametrize("datatype", ["string", "string[]"])
def test_exports_reported_values(tmp_path, monkeypatch, datatype):
    enum_name, literals = _export(["NO_BLANK", "WITH_ BLANK", "SMÖRGÅSTÅRTA"], tmp_path, monkeypatch, datatype)
    assert enum_name == "SignalValues"
    assert literals[:2] == ["NO_BLANK", "WITH__BLANK"]
    assert len(literals) == 3
    assert all(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value) for value in literals)


def test_resolves_case_space_digit_and_escape_collisions(tmp_path, monkeypatch):
    values = ["WITH BLANK", "WITH_BLANK", "with_blank", "WITH_BLANK_2", "d123", "123", "_Legacy", "Legacy"]
    _, literals = _export(values, tmp_path, monkeypatch)
    assert len({_key(value) for value in literals}) == len(values)
    assert literals[0] == "WITH_BLANK"
    assert literals[3] == "WITH_BLANK_2"
    assert literals[4] == "d123"


def test_encoded_names_do_not_take_existing_literal_names(tmp_path, monkeypatch):
    values = ["ö", "vss_c3b6", "VSS_C3B6", "vss_c3b6_2", ""]
    _, literals = _export(values, tmp_path, monkeypatch)
    assert len({_key(value) for value in literals}) == len(values)
    assert literals[1] == "vss_c3b6"
    assert literals[3] == "vss_c3b6_2"


def test_literals_do_not_collide_with_local_type_or_module(tmp_path, monkeypatch):
    enum_name, literals = _export(["SignalValues", "_SignalValues", "Signal_M", "_Signal_M"], tmp_path, monkeypatch)
    keys = {_key(value) for value in literals}
    assert len(keys) == 4
    assert _key(enum_name) not in keys
    assert "signal_m" not in keys


def test_mapping_is_deterministic_and_keeps_value_order(tmp_path, monkeypatch):
    values = ["RIGHT", "ö", "LEFT", "right", "", "_module", "module"]
    first = _export(values, tmp_path, monkeypatch)[1]
    second = _export(values, tmp_path, monkeypatch)[1]
    assert first == second
    assert first[0] == "RIGHT"
    assert first[2] == "LEFT"
    assert first[5] == "_module"
    assert len({_key(value) for value in first}) == len(values)
