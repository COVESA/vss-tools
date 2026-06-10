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
        topics_file = tmp_path / "ros_test_topics.txt"
        topics_file.write_text("# includes only branch A\n" "A.*", encoding="utf-8")

        cmd += f" --output {output}"
        cmd += f" --topics-file {topics_file} --topics A.* --topics A.Double --topics fqn:A.Uint8"
        cmd += "  --mode aggregate --srv both --expand --srv-use-msg --exclude-topics Z.*"
        cmd += "  --topics-case-sensitive --topics name:Uint16 --topics Uint32"
        cmd += "  --topics *:Float --topics regex:^A\\.Int16\\..*$ --topics Uint32"
        cmd += f"  --output-vspec {tmp_path / 'transformed.vspec'} --package-name vss_interfaces"
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

    # render_get_srv: latest-single-value service. The request carries NO time-window
    # fields (the Get always returns the latest single value), and the flattened
    # response field is present when use_msg=False.
    fields = [{"type": "uint8", "name": "val", "comment": "desc"}]
    srv = render_get_srv("pkg", "Msg", fields, use_msg=False)
    assert "uint8 val" in srv
    assert "start_time_seconds" not in srv
    assert "end_time_seconds" not in srv

    # render_get_srv with use_msg=True nests the message as a single latest value
    srv_use_msg = render_get_srv("pkg", "Msg", fields, use_msg=True)
    assert "Msg data" in srv_use_msg
    assert "Msg[] data" not in srv_use_msg
    assert "Latest data" in srv_use_msg

    srv2 = render_set_srv("pkg", "Msg", fields, use_msg=False)
    assert "uint8 val" in srv2


def test_ros2interface_timeseries_helper_functions():
    """Exercise the inline rendering helpers added for --timeseries.

    These cover the pure-string rendering logic (no CLI, no filesystem) so
    coverage of the timeseries code path is recorded against this file.
    """
    pytest.importorskip("anytree")
    src_dir = HERE.parents[1] / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from vss_tools.exporters.ros2interface import (  # noqa: PLC0415
        DEFAULT_TIMESTAMP,
        Timestamp,
        TimestampProperty,
        _timestamp_suffixes,
        render_get_timeseries_srv,
        render_set_timeseries_srv,
        render_timeseries_msg,
        timeseries_msg_name,
        timeseries_srv_names,
    )

    # --- naming helpers ---
    assert timeseries_msg_name("VehicleSpeed") == "VehicleSpeedTimeseries.msg"

    ts_base, get_srv, set_srv = timeseries_srv_names("VehicleSpeed")
    assert ts_base == "VehicleSpeedTimeseries"
    assert get_srv == "GetVehicleSpeedTimeseries.srv"
    assert set_srv == "SetVehicleSpeedTimeseries.srv"

    # --- suffix derivation: default schema (seconds + nanoseconds) ---
    suffixes_default = _timestamp_suffixes(DEFAULT_TIMESTAMP)
    assert suffixes_default == [("int64", "seconds"), ("int64", "nanoseconds")]

    # --- timeseries .msg rendering, default timestamp schema ---
    ts_msg = render_timeseries_msg(
        base_msg_name="VehicleSpeed",
        signal_fqn="Vehicle.Speed",
        timestamp_schema=DEFAULT_TIMESTAMP,
    )
    assert "Timeseries wrapper for Vehicle.Speed" in ts_msg
    assert "int64 window_start_seconds" in ts_msg
    assert "int64 window_start_nanoseconds" in ts_msg
    assert "int64 window_end_seconds" in ts_msg
    assert "int64 window_end_nanoseconds" in ts_msg
    assert "VehicleSpeed[] samples" in ts_msg
    # generated-header line is always present
    assert "AUTO-GENERATED by VSS-TOOLS" in ts_msg

    # --- Get<>Timeseries.srv rendering ---
    # Unlike the latest-single Get, the timeseries Get keeps the time-window request.
    get_ts_srv = render_get_timeseries_srv(
        base_msg_name="VehicleSpeed",
        timestamp_schema=DEFAULT_TIMESTAMP,
    )
    # request side
    assert "int64 start_time_seconds" in get_ts_srv
    assert "int64 start_time_nanoseconds" in get_ts_srv
    assert "int64 end_time_seconds" in get_ts_srv
    assert "int64 end_time_nanoseconds" in get_ts_srv
    assert "uint32 max_samples" in get_ts_srv
    assert "bool prefer_newest" in get_ts_srv
    # request/response separator
    assert "---" in get_ts_srv
    # response side
    assert "VehicleSpeedTimeseries timeseries" in get_ts_srv
    assert "bool success" in get_ts_srv
    assert "string message" in get_ts_srv

    # --- Set<>Timeseries.srv rendering ---
    set_ts_srv = render_set_timeseries_srv(base_msg_name="VehicleSpeed")
    # request side
    assert "VehicleSpeedTimeseries timeseries" in set_ts_srv
    assert "bool prefer_newest" in set_ts_srv
    # response side
    assert "bool success" in set_ts_srv
    assert "string message" in set_ts_srv
    assert "uint32 samples_accepted" in set_ts_srv
    # request/response separator
    assert "---" in set_ts_srv

    # --- custom timestamp schema: confirm suffix propagation through all three renderers ---
    custom_schema = Timestamp(
        fqn="CustomTypes.MyTime",
        properties=[
            TimestampProperty(name="epoch_s", ros_name="timestamp_epoch_s", ros_type="int64", comment="Epoch seconds"),
            TimestampProperty(name="nanos", ros_name="timestamp_nanos", ros_type="int64", comment="Nanoseconds"),
        ],
    )
    assert _timestamp_suffixes(custom_schema) == [("int64", "epoch_s"), ("int64", "nanos")]

    custom_ts_msg = render_timeseries_msg("VehicleSpeed", "Vehicle.Speed", timestamp_schema=custom_schema)
    assert "int64 window_start_epoch_s" in custom_ts_msg
    assert "int64 window_start_nanos" in custom_ts_msg
    assert "int64 window_end_epoch_s" in custom_ts_msg
    assert "int64 window_end_nanos" in custom_ts_msg
    # default suffixes must NOT appear when a custom schema is in use
    assert "window_start_seconds" not in custom_ts_msg
    assert "window_start_nanoseconds" not in custom_ts_msg

    custom_get_srv = render_get_timeseries_srv("VehicleSpeed", timestamp_schema=custom_schema)
    assert "int64 start_time_epoch_s" in custom_get_srv
    assert "int64 start_time_nanos" in custom_get_srv
    assert "int64 end_time_epoch_s" in custom_get_srv
    assert "int64 end_time_nanos" in custom_get_srv
    # max_samples/prefer_newest are independent of the schema, still present
    assert "uint32 max_samples" in custom_get_srv
    assert "bool prefer_newest" in custom_get_srv

    # --- single-property schema: confirm the loop still produces one of each (no off-by-one) ---
    single_prop_schema = Timestamp(
        fqn="X.OnlySeconds",
        properties=[
            TimestampProperty(name="seconds", ros_name="timestamp_seconds", ros_type="int64", comment="Seconds"),
        ],
    )
    single_ts_msg = render_timeseries_msg("A", "X.A", timestamp_schema=single_prop_schema)
    # exactly one window_start and one window_end field
    assert single_ts_msg.count("window_start_seconds") == 1
    assert single_ts_msg.count("window_end_seconds") == 1


def test_ros2interface_srv_get_latest_single_value(tmp_path):
    """End-to-end: --srv get produces a Get<Msg>.srv with an empty request (no time
    window) and a single latest-value response."""
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
            "get",
        ],
        check=True,
    )
    get_srv = out / "vss_interfaces" / "srv" / "GetASpeed.srv"
    assert get_srv.exists(), f"Missing {get_srv}"
    text = get_srv.read_text(encoding="utf-8")
    # single latest value response, no array, no time-window request fields
    assert "ASpeed data" in text
    assert "ASpeed[] data" not in text
    assert "start_time_seconds" not in text
    assert "end_time_seconds" not in text


def test_ros2interface_timeseries_cli_default_schema(tmp_path):
    """End-to-end CLI smoke test for --timeseries both with the built-in timestamp defaults.

    Verifies that --timeseries produces the expected files per signal and
    that latest-single services are NOT generated when --srv is omitted.
    """
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
            "--timeseries",
            "both",
        ],
        check=True,
    )

    # Expected package dir is <out>/<default-package-name>
    pkg_dir = out / "vss_interfaces"
    msg_dir = pkg_dir / "msg"
    srv_dir = pkg_dir / "srv"

    # Point-in-time .msg is present for every signal in _SIMPLE_VSPEC.
    for signal in ("ASpeed", "ACodes", "AMonth"):
        assert (msg_dir / f"{signal}.msg").exists(), f"Missing {signal}.msg"
        assert (msg_dir / f"{signal}Timeseries.msg").exists(), f"Missing {signal}Timeseries.msg"
        assert (srv_dir / f"Get{signal}Timeseries.srv").exists(), f"Missing Get{signal}Timeseries.srv"
        assert (srv_dir / f"Set{signal}Timeseries.srv").exists(), f"Missing Set{signal}Timeseries.srv"

    # --srv was not passed, so latest-single services must NOT be generated.
    assert not (srv_dir / "GetASpeed.srv").exists()
    assert not (srv_dir / "SetASpeed.srv").exists()

    # Spot-check the content of one generated timeseries .msg.
    ts_text = (msg_dir / "ASpeedTimeseries.msg").read_text(encoding="utf-8")
    assert "int64 window_start_seconds" in ts_text
    assert "int64 window_end_nanoseconds" in ts_text
    assert "ASpeed[] samples" in ts_text


def test_ros2interface_timeseries_cli_get_only(tmp_path):
    """--timeseries get emits the wrapper .msg + Get service, but NOT the Set service."""
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
            "--timeseries",
            "get",
        ],
        check=True,
    )
    srv_dir = out / "vss_interfaces" / "srv"
    msg_dir = out / "vss_interfaces" / "msg"
    assert (msg_dir / "ASpeedTimeseries.msg").exists()
    assert (srv_dir / "GetASpeedTimeseries.srv").exists()
    assert not (srv_dir / "SetASpeedTimeseries.srv").exists()


def test_ros2interface_timeseries_cli_set_only(tmp_path):
    """--timeseries set emits the wrapper .msg + Set service, but NOT the Get service."""
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
            "--timeseries",
            "set",
        ],
        check=True,
    )
    srv_dir = out / "vss_interfaces" / "srv"
    msg_dir = out / "vss_interfaces" / "msg"
    assert (msg_dir / "ASpeedTimeseries.msg").exists()
    assert (srv_dir / "SetASpeedTimeseries.srv").exists()
    assert not (srv_dir / "GetASpeedTimeseries.srv").exists()


def test_ros2interface_srv_and_timeseries_combined(tmp_path):
    """--srv and --timeseries are independent and can be combined in one run."""
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
            "get",
            "--timeseries",
            "both",
        ],
        check=True,
    )
    srv_dir = out / "vss_interfaces" / "srv"
    msg_dir = out / "vss_interfaces" / "msg"
    # latest-single Get present; latest-single Set NOT (only --srv get)
    assert (srv_dir / "GetASpeed.srv").exists()
    assert not (srv_dir / "SetASpeed.srv").exists()
    # timeseries trio present
    assert (msg_dir / "ASpeedTimeseries.msg").exists()
    assert (srv_dir / "GetASpeedTimeseries.srv").exists()
    assert (srv_dir / "SetASpeedTimeseries.srv").exists()


def test_ros2interface_timeseries_cli_aggregate_mode(tmp_path):
    """--timeseries should also work in aggregate mode (one .msg per parent branch).

    The existing test-ros2-interface.py tests only cover leaf mode; this fills the gap.
    """
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
            "aggregate",
            "--timeseries",
            "both",
        ],
        check=True,
    )

    pkg_dir = out / "vss_interfaces"
    msg_dir = pkg_dir / "msg"
    srv_dir = pkg_dir / "srv"

    # In aggregate mode, signals under branch A produce a single A.msg + ATimeseries.msg.
    assert (msg_dir / "A.msg").exists()
    assert (msg_dir / "ATimeseries.msg").exists()
    assert (srv_dir / "GetATimeseries.srv").exists()
    assert (srv_dir / "SetATimeseries.srv").exists()

    ts_text = (msg_dir / "ATimeseries.msg").read_text(encoding="utf-8")
    assert "A[] samples" in ts_text


def test_ros2interface_timeseries_cli_with_topic_filter(tmp_path):
    """--timeseries should respect --topics filtering: only matched signals get timeseries files."""
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
            "--topics",
            "A.Speed",
            "--timeseries",
            "both",
        ],
        check=True,
    )

    pkg_dir = out / "vss_interfaces"
    msg_dir = pkg_dir / "msg"
    srv_dir = pkg_dir / "srv"

    # Only A.Speed (and its timeseries companions) are generated.
    assert (msg_dir / "ASpeed.msg").exists()
    assert (msg_dir / "ASpeedTimeseries.msg").exists()
    assert (srv_dir / "GetASpeedTimeseries.srv").exists()
    assert (srv_dir / "SetASpeedTimeseries.srv").exists()

    # Other signals must NOT be generated.
    assert not (msg_dir / "ACodes.msg").exists()
    assert not (msg_dir / "AMonthTimeseries.msg").exists()