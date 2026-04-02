# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import filecmp
import pathlib
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / "test_units.yaml"
TEST_QUANT = HERE / "test_quantities.yaml"
DEFAULT_TEST_FILE = "test.vspec"


def default_directories() -> list:
    directories = []
    for path in HERE.iterdir():
        if path.is_dir():
            if list(path.rglob(DEFAULT_TEST_FILE)):
                # Exclude directories with custom made python file
                if not list(path.rglob("*.py")):
                    directories.append(path)
    return directories


# Use directory name as test name
def idfn(directory: pathlib.PosixPath):
    return directory.name


def run_exporter(directory, exporter, tmp_path):
    vspec = directory / DEFAULT_TEST_FILE
    types = directory / "types.vspec"
    output = tmp_path / f"out.{exporter}"
    expected = directory / f"expected.{exporter}"
    if not expected.exists():
        # If you want find directory/exporter combinations not yet covered enable the assert
        # assert False, f"Folder {expected} not found"
        return
    cmd = f"vspec export {exporter} -u {TEST_UNITS} -q {TEST_QUANT} --vspec {vspec} "
    if types.exists():
        cmd += f" --types {types}"
    if exporter in ["apigear"]:
        cmd += f" --output-dir {output}"
    elif exporter in ["samm"]:
        cmd += f" --target-folder {output}"
    elif exporter in ["ros2interface"]:
        # Generate a topics file for test, shall not be checked in
        topics_file = directory / "ros_test_topics.txt"
        topics_file.write_text("# includes only branch A\n" "A.*", encoding="utf-8")

        cmd += f" --output {output}"
        cmd += f" --topics-file {topics_file} --topics A.* --topics A.Double --topics fqn:A.Uint8"
        cmd += "  --mode aggregate --srv both --expand --srv-use-msg --exclude-topics Z.*"
        cmd += "  --topics-case-sensitive --topics name:Uint16 --topics Uint32"
        cmd += "  --topics *:Float --topics regex:^A\\.Int16\\..*$ --topics Uint32"
        cmd += "  --output-vspec ./out/transformed.vspec --package-name vss_interfaces"
    else:
        cmd += f" --output {output}"

    subprocess.run(cmd.split(), check=True)
    if exporter in ["apigear", "samm"]:
        dcmp = filecmp.dircmp(output, expected)
        assert not (dcmp.diff_files or dcmp.left_only or dcmp.right_only)
    elif exporter in ["ros2interface"]:
        dcmp = filecmp.dircmp(output, expected)
        assert not (dcmp.diff_files)
    else:
        assert filecmp.cmp(output, expected)


@pytest.mark.parametrize("directory", default_directories(), ids=idfn)
def test_exporters(directory, tmp_path):
    # Run all "supported" exporters, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on target
    exporters = [
        "ros2interface",
        "apigear",
        "json",
        "jsonschema",
        "ddsidl",
        "plantuml",
        "csv",
        "yaml",
        "franca",
        "go",
        "samm",
    ]

    for exporter in exporters:
        run_exporter(directory, exporter, tmp_path)


# ---------- ros2interface coverage-boosting tests ----------------

_SIMPLE_VSPEC = (
    "A:\n  type: branch\n  description: Branch A.\n"
    "A.Speed:\n  datatype: uint8\n  type: sensor\n  description: Speed signal.\n"
    "A.Codes:\n  datatype: uint8[]\n  type: sensor\n  arraysize: 5\n  description: Codes.\n"
    "A.Month:\n  datatype: string\n  type: sensor\n"
    "  allowed: ['Jan', 'Feb', 'Mar']\n  description: Month.\n"
)


def _write_vspec(tmp_path: Path, text: str = _SIMPLE_VSPEC) -> Path:
    p = tmp_path / "test.vspec"
    p.write_text(text, encoding="utf-8")
    return p


def test_ros2interface_leaf_mode_no_srv_use_msg(tmp_path):
    vspec = _write_vspec(tmp_path)
    out = tmp_path / "out"
    subprocess.run(
        [
            "vspec",
            "export",
            "ros2interface",
            "-u",
            str(TEST_UNITS),
            "-q",
            str(TEST_QUANT),
            "--vspec",
            str(vspec),
            "--output",
            str(out),
            "--mode",
            "leaf",
            "--srv",
            "both",
            "--no-srv-use-msg",
        ],
        check=True,
    )


def test_ros2interface_no_match_warning(tmp_path):
    vspec = _write_vspec(tmp_path)
    result = subprocess.run(
        [
            "vspec",
            "export",
            "ros2interface",
            "-u",
            str(TEST_UNITS),
            "-q",
            str(TEST_QUANT),
            "--vspec",
            str(vspec),
            "--output",
            str(tmp_path / "out"),
            "--topics",
            "NONEXISTENT_XYZ_SIGNAL",
        ],
        capture_output=True,
        text=True,
    )
    assert "No VSS signals matched" in (result.stdout + result.stderr)


def test_ros2interface_output_vspec_with_arraysize(tmp_path):
    vspec = _write_vspec(tmp_path)
    out_vspec = tmp_path / "transformed.vspec"
    subprocess.run(
        [
            "vspec",
            "export",
            "ros2interface",
            "-u",
            str(TEST_UNITS),
            "-q",
            str(TEST_QUANT),
            "--vspec",
            str(vspec),
            "--output",
            str(tmp_path / "out"),
            "--mode",
            "leaf",
            "--output-vspec",
            str(out_vspec),
        ],
        check=True,
    )
    assert out_vspec.exists()
    assert "arraysize" in out_vspec.read_text()


def test_ros2interface_helper_functions():
    pytest.importorskip("anytree")  # skip gracefully when vss_tools deps are unavailable
    src_dir = HERE.parents[1] / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from vss_tools.exporters.ros2interface import (  # noqa: PLC0415
        TopicMatcher,
        _compile_rule,
        _read_patterns_file,
        build_timestamp_fields,
        map_vss_to_ros_field,
        render_get_srv,
        render_msg_file,
        render_set_srv,
    )

    assert map_vss_to_ros_field("uint8", 4) == "uint8[4]"
    assert map_vss_to_ros_field("uint8[]", None) == "uint8[]"

    rule_fqn = _compile_rule("fqn:A.B", False)
    assert rule_fqn("B", "A.B") and rule_fqn("C", "A.B.C") and not rule_fqn("X", "X.Y")

    assert _compile_rule("Speed", False)("Speed", "A.Speed")
    assert not _compile_rule("Speed", False)("speed", "A.speed")
    assert _compile_rule("Sp*", False)("Speed", "A.Speed")

    assert _compile_rule("fqn:a.b", True)("B", "A.B")

    assert TopicMatcher([], []).matches("A.B.C")

    m = TopicMatcher(["A.*"], ["A.B"])
    assert not m.matches("A.B") and m.matches("A.C")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("   ")
        empty_p = Path(f.name)
    assert _read_patterns_file(empty_p) == []
    empty_p.unlink()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("- A.Speed\n- A.Brake\n")
        yaml_p = Path(f.name)
    assert "A.Speed" in _read_patterns_file(yaml_p)
    yaml_p.unlink()

    assert "Allowed" in render_msg_file("X", [{"type": "uint8", "name": "v", "comment": ""}], [], ["Allowed: a"])

    assert build_timestamp_fields()[0]["name"] == "timestamp_seconds"

    fields = [{"type": "uint8", "name": "val", "comment": "desc"}]
    srv = render_get_srv("pkg", "Msg", fields, use_msg=False)
    assert "uint8 val" in srv and "int64 start_time_seconds" in srv

    srv2 = render_set_srv("pkg", "Msg", fields, use_msg=False)
    assert "uint8 val" in srv2
