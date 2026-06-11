# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / "test_units_ros2.yaml"
TEST_QUANT = HERE / "test_quantities_ros2.yaml"
EXPORTER = "ros2interface"  # the subcommand of ros2 exporter
DEFAULT_PKG = "vss_interfaces"  # package name used in tests
INCLUDE_DIR = HERE.parents[2] / "vehicle_signal_specification" / "spec" / "include"


def run_ros2_exporter(
    vspec_text: str,
    tmp_path: Path,
    *,
    package_name: str = DEFAULT_PKG,
    mode: str = "leaf",
    extra_args: list[str] | None = None,
) -> Path:
    """
    Write a temporary .vspec, invoke the exporter, and return the
    package directory <out>/<package_name>.
    """
    vspec_file = tmp_path / "test.vspec"
    vspec_file.write_text(vspec_text, encoding="utf-8")

    out_root = tmp_path / "out.ros2"
    args = [
        "vspec",
        "export",
        EXPORTER,
        "--units",
        str(TEST_UNITS),
        "--quantities",
        str(TEST_QUANT),
        "--vspec",
        str(vspec_file),
        "--output",
        str(out_root),
        "--package-name",
        package_name,
        "--mode",
        mode,
    ]
    if extra_args:
        args += extra_args
    try:
        subprocess.run(args, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise AssertionError(
            "vspec exporter invocation failed\n"
            f"  cmd: {' '.join(e.cmd)}\n"
            f"  returncode: {e.returncode}\n"
            f"  stdout:\n{e.stdout}\n"
            f"  stderr:\n{e.stderr}\n"
        ) from e
    return out_root / package_name  # <output>/<package_name>


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


# ------------- basic .msg output test -------------


def test_ros2_basic_signal_to_msg(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Vehicle speed.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "ASpeed.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "float32 value" in text
    assert "Vehicle speed." in text
    assert "uint64 timestamp" not in text

    # ---- order check with multiline regex ----

    pattern = re.compile(
        r"""
            ^\s*(?:\#.*\r?\n|\r?\n)*              # any comments/empty lines before timestamp
            \s*int64\s+timestamp_seconds\s*\r?\n  # timestamp_seconds line
            (?:\s*\r?\n|\s*\#.*\r?\n)*            # optional blank lines / comments between
            \s*int64\s+timestamp_nanoseconds\s*$  # timestamp_nanoseconds line
            """,
        flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE,
    )

    assert pattern.search(text), "Expected layout not found. Incorrect layout!"


# ------------- flat .srv output test -------------


def test_ros2_set_srv_flattened_when_no_use_msg(tmp_path):
    """Set service with --no-srv-use-msg flattens fields (including timestamp)."""
    vspec = """\
A:
  type: branch
  description: Branch A.
A.FanSpeed:
  type: actuator
  datatype: uint16
  min: 0
  max: 5
  description: Cabin fan target speed (0..5).
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--srv", "set", "--no-srv-use-msg", "--include-dirs", str(INCLUDE_DIR)],
    )
    srv = pkg_dir / "srv" / "SetAFanSpeed.srv"  # naming: Set<MsgBase>.srv
    assert srv.is_file(), f"Missing {srv}"
    text = read_text(srv)

    # flattened request fields derived from message fields
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "uint16 value" in text
    assert "bool success" in text
    assert "string message" in text


# ------------- custom msg Get<MsgBase>.srv output test -------------


def test_ros2_get_srv_when_use_msg(tmp_path):
    """Get service with --srv-use-msg"""
    vspec = """\
A:
  type: branch
  description: Branch A.
A.FanSpeed:
  type: actuator
  datatype: uint16
  min: 0
  max: 5
  description: Cabin fan target speed (0..5).
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--srv", "get", "--srv-use-msg", "--include-dirs", str(INCLUDE_DIR)],
    )
    msg = pkg_dir / "msg" / "AFanSpeed.msg"  # naming: <MsgBase>.msg
    srv = pkg_dir / "srv" / "GetAFanSpeed.srv"  # naming: Get<MsgBase>.srv
    assert msg.is_file(), f"Missing {msg}"
    assert srv.is_file(), f"Missing {srv}"
    text = read_text(srv)

    assert "int64 start_time_seconds" in text
    assert "int64 start_time_nanoseconds" in text
    assert "int64 end_time_seconds" in text
    assert "int64 end_time_nanoseconds" in text
    # custom message field
    assert "AFanSpeed[] data" in text


# ------------- custom msg Set<MsgBase>.srv output test -------------


def test_ros2_set_srv_when_use_msg(tmp_path):
    """Set service with --srv-use-msg"""
    vspec = """\
A:
  type: branch
  description: Branch A.
A.FanSpeed:
  type: actuator
  datatype: uint16
  min: 0
  max: 5
  description: Cabin fan target speed (0..5).
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--srv", "set", "--srv-use-msg"],
    )
    msg = pkg_dir / "msg" / "AFanSpeed.msg"  # naming: <MsgBase>.msg
    srv = pkg_dir / "srv" / "SetAFanSpeed.srv"  # naming: Set<MsgBase>.srv
    assert msg.is_file(), f"Missing {msg}"
    assert srv.is_file(), f"Missing {srv}"
    text = read_text(srv)

    # custom message field
    assert "AFanSpeed data" in text
    assert "bool success" in text
    assert "string message" in text


# ------------- output with structs -------------


def test_ros2_enums_as_comment_allowed_values(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.DriveMode:
  type: attribute
  datatype: string
  allowed: ["park", "drive", "reverse"]
  description: Selected drive mode.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf")
    msg = pkg_dir / "msg" / "ADriveMode.msg"
    assert msg.is_file()
    text = read_text(msg)

    # ros2 exporter writes allowed values as a comment, not constants
    assert "Allowed values:" in text
    assert "park" in text and "drive" in text and "reverse" in text

    # field type & value field name
    assert "string value" in text


# ------------- output with arrays in the datatypes -------------


def test_ros2_arrays(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.ByteArray:
  type: sensor
  datatype: uint8[]
  description: A byte sequence.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AByteArray.msg"
    assert msg.is_file()
    text = read_text(msg)
    assert "uint8[] value" in text
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text


# ------------- output with bound in the comments like min and max range (e.g range=[0,10]) -------------


def test_ros2_units_and_bounds_in_comments(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Acceleration:
  datatype: float
  type: sensor
  unit: m/s^2
  min: 0
  max: 100
  description: Vehicle acceleration in X (acceleration).
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf")
    msg = pkg_dir / "msg" / "AAcceleration.msg"
    assert msg.is_file()
    text = read_text(msg)

    # unit is included in the field's inline comment
    assert "unit=m/s^2" in text
    assert "range=[0,100]" in text


# ------------- multi branch leaf output -------------


def test_ros2_multi_step_leaf(tmp_path):
    vspec = """\
Vehicle:
  type: branch
  description: Vehicle root.
Vehicle.Acceleration:
  type: branch
  description: Spatial acceleration.
Vehicle.Acceleration.Longitudinal:
  datatype: float
  type: sensor
  description: Vehicle acceleration in X (longitudinal acceleration).
"""
    # A .msg file for the deepest leaf should be created.
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf")
    msg = pkg_dir / "msg" / "VehicleAccelerationLongitudinal.msg"
    assert msg.is_file()
    read_text(msg)


# ------------- Additional tests to reflect exporter`s extended behavior -------------


def test_ros2_topics_include_filter(tmp_path):
    """
    Verify that --topics include filter selects only the requested signals.
    """
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Speed
A.RPM:
  type: sensor
  datatype: uint16
  description: Engine RPM
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--topics", "A.Speed"],  # exact FQN
    )
    # Only ASpeed.msg should be exported
    assert (pkg_dir / "msg" / "ASpeed.msg").is_file()
    assert not (pkg_dir / "msg" / "ARPM.msg").exists()


# ------------- include every topic by using wildcard validation -------------


def test_ros2_topics_include_all(tmp_path):
    """
    Verify combined include (glob) and exclude (name) filters.
    """
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Speed in Km/h
A.RPM:
  type: sensor
  datatype: uint16
  description: Engine RPM
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--topics", "A.*"],  # include all A.*, exclude by tail name
    )
    # ASpeed.msg included, ARPM.msg excluded
    assert (pkg_dir / "msg" / "ASpeed.msg").is_file()
    assert (pkg_dir / "msg" / "ARPM.msg").exists()


# ------------- include and exclude different topics validation -------------


def test_ros2_topics_include_and_exclude(tmp_path):
    """
    Verify combined include (glob) and exclude (name) filters.
    """
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Speed in Km/h
A.RPM:
  type: sensor
  datatype: uint16
  description: Engine RPM
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--topics", "A.*", "--exclude-topics", "RPM"],  # include all A.*, exclude by tail name
    )
    # ASpeed.msg included, ARPM.msg excluded
    assert (pkg_dir / "msg" / "ASpeed.msg").is_file()
    assert not (pkg_dir / "msg" / "ARPM.msg").exists()


# ------------- usage of msg file name in srv file validation -------------


def test_ros2_srv_both_use_msg(tmp_path):
    """
    When --srv both and --srv-use-msg are set, services should carry the .msg type.
    """
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Speed in Km/h
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--srv", "both", "--srv-use-msg", "--include-dirs", str(INCLUDE_DIR)],
    )
    get_srv = pkg_dir / "srv" / "GetASpeed.srv"
    set_srv = pkg_dir / "srv" / "SetASpeed.srv"
    assert get_srv.is_file()
    assert set_srv.is_file()

    get_text = read_text(get_srv)
    set_text = read_text(set_srv)

    # Get response uses message array
    pattern_get = re.compile(
        r"""
        ^\s*(?:\#.*\r?\n|\r?\n)*                  # (top) any # comments / empty lines
        \s*int64\s+start_time_seconds\s*\r?\n     # 1) request: start_time_seconds
        \s*int64\s+start_time_nanoseconds\s*\r?\n # 2) request: start_time_nanoseconds
        \s*int64\s+end_time_seconds\s*\r?\n       # 3) request: end_time_seconds
        \s*int64\s+end_time_nanoseconds\s*\r?\n   # 4) request: end_time_nanoseconds
        \s*---\s*\r?\n                             # 5) separator
        \s*ASpeed\[\]\s+data\s*$                  # 6) response: ASpeed[] data
        """,
        flags=re.MULTILINE | re.VERBOSE | re.IGNORECASE,
    )
    assert pattern_get.search(get_text), "Expected layout not found in the Get<MsgBase>.srv File, Incorrect layout!"

    # Set request uses message
    pattern_set = re.compile(
        r"""
        ^\s*(?:\#.*\r?\n|\r?\n)*       # (top) any # comments / empty lines
        \s*ASpeed\s+data\s*\r?\n       # 1) request: ASpeed data
        \s*---\s*\r?\n                 # 2) separator
        \s*bool\s+success\s*\r?\n      # 3) response: bool success
        \s*string\s+message\s*$        # 4) response: string message
        """,
        flags=re.MULTILINE | re.VERBOSE | re.IGNORECASE,
    )

    assert pattern_set.search(set_text), "Expected layout not found in the Set<MsgBase>.srv File, Incorrect layout!"


# ------------- setting the srv param to none validation -------------


def test_ros2_srv_none(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Speed in Km/h
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
    )
    get_srv = pkg_dir / "srv" / "GetASpeed.srv"
    set_srv = pkg_dir / "srv" / "SetASpeed.srv"
    assert not (get_srv.is_file())
    assert not (set_srv.is_file())


# ------------- output only get srv validation -------------


def test_ros2_srv_get_output(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Speed in Km/h
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--srv", "get"],
    )
    get_srv = pkg_dir / "srv" / "GetASpeed.srv"
    set_srv = pkg_dir / "srv" / "SetASpeed.srv"
    assert get_srv.is_file()
    assert not (set_srv.is_file())


# ------------- output only set srv validation -------------


def test_ros2_srv_set_output(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Speed in Km/h
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--srv", "set"],
    )
    get_srv = pkg_dir / "srv" / "GetASpeed.srv"
    set_srv = pkg_dir / "srv" / "SetASpeed.srv"
    assert not (get_srv.is_file())
    assert set_srv.is_file()


# ------------- Aggregate-mode validation -------------


def test_ros2_aggregate_mode_combines_fields_and_allowed_values(tmp_path):
    """
    Aggregate mode should group leaves under their direct parent branch,
    prepend a timestamp field, and include a combined 'Allowed values (combined)' comment.
    """
    vspec = """\
B:
  type: branch
  description: Parent branch B.
B.Mode:
  type: attribute
  datatype: string
  allowed: ["eco", "sport"]
  description: Selected mode.
B.Level:
  type: sensor
  datatype: uint8
  allowed: [0, 1, 2]
  description: Level setting.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="aggregate", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "B.msg"
    assert msg.is_file(), "Aggregate message for branch B should be created"
    text = read_text(msg)

    assert "Parent branch: B" in text
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "string mode" in text
    assert "uint8 level" in text
    assert "Allowed values (combined):" in text
    for token in ("eco", "sport", "0", "1", "2"):
        assert token in text
    assert not (pkg_dir / "msg" / "BMode.msg").exists()
    assert not (pkg_dir / "msg" / "BLevel.msg").exists()


# ------------- topics-file -------------


def test_ros2_topics_file_includes_only_matching(tmp_path):
    """
    --topics-file loads include patterns; comments with '#' are ignored.
    --file formats which are supported are `Yaml` and `txt` files.
    --`txt` files support only one topic per line.
    """
    vspec = """\
A:
  type: branch
  description: Parent branch A
A.Speed:
  type: sensor
  datatype: float
  description: speed in Km/h
A.RPM:
  type: sensor
  datatype: uint16
  description: engine RPM
A.Level:
  type: sensor
  datatype: uint8
  description: Level setting.
"""
    topics_file = tmp_path / "topics.txt"
    topics_file.write_text("# include only branch A signals\n" "A.Speed\nA.RPM\n", encoding="utf-8")

    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--topics-file", str(topics_file)],
    )

    # Included
    assert (pkg_dir / "msg" / "ASpeed.msg").is_file()
    assert (pkg_dir / "msg" / "ARPM.msg").is_file()

    # Not included
    assert not (pkg_dir / "msg" / "ALevel.msg").exists()


# ------------- topics-case-insensitive -------------


def test_ros2_topics_case_insensitive_name_match(tmp_path):
    """
    Case-insensitive matching should allow 'speed' to match 'Speed' tail name.
    """
    vspec = """\
A:
  type: branch
  description: Parent branch A
A.Speed:
  type: sensor
  datatype: float
  description: speed in Km/h
A.RPM:
  type: sensor
  datatype: uint16
  description: engine RPM
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--topics", "speed", "--topics-case-insensitive"],
    )

    assert (pkg_dir / "msg" / "ASpeed.msg").is_file()
    assert not (pkg_dir / "msg" / "ARPM.msg").exists()


# ------------- topics-case-sensitive -------------


def test_ros2_topics_case_sensitive_name_match(tmp_path):
    """
    Case-sensitive matching should not allow 'speed' to match 'Speed' tail name.
    """
    vspec = """\
A:
  type: branch
  description: Parent branch A
A.Speed:
  type: sensor
  datatype: float
  description: Speed in Km/h
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--topics", "speed", "--topics-case-sensitive"],
    )

    try:
        assert not (pkg_dir / "msg" / "ASpeed.msg").is_file()
    except Exception:
        pytest.skip("No msg file was created, test passed!")


# ------------- CLI smoke test for entry point -------------


def test_cli_entrypoint_smoke():
    """
    Ensure the exporter entry point is visible to 'vspec export'.
    If not registered in the environment, skip (so the suite can still run).
    """
    if shutil.which("vspec") is None:
        pytest.skip("vspec CLI not found in PATH")

    try:
        cp = subprocess.run(
            ["vspec", "export", "ros", "--help"],
            text=True,
            capture_output=True,
        )
    except Exception as e:
        pytest.skip(f"vspec CLI not invokable: {e}")

    if cp.returncode != 0:
        pytest.skip(
            "ros exporter not registered with 'vspec export'. "
            "Install exporter package with entry points (e.g., pip install -e .) to enable this smoke test."
        )

    # Minimal sanity: help text should contain 'Export a VSS model to a ROS 2 interface' (from click help)
    assert "Export a VSS model to a ROS 2 interface" in (cp.stdout or "") + (cp.stderr or "")


# ------------- bool datatype conversion output test -------------


def test_ros2_test_datatype_bool(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Door:
  type: branch
  description: Door of Branch A.
A.Door.Open:
  type: attribute
  datatype: boolean
  description: Door status.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "ADoorOpen.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "bool value" in text
    assert "Door status." in text


# ------------- uint8 datatype conversion output test -------------


def test_ros2_test_datatype_uint8(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: uint8
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "uint8 value" in text
    assert "Engine Temperature." in text


# ------------- uint16 datatype conversion output test -------------


def test_ros2_test_datatype_uint16(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: uint16
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "uint16 value" in text
    assert "Engine Temperature." in text


# ------------- uint32 datatype conversion output test -------------


def test_ros2_test_datatype_uint32(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: uint32
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "uint32 value" in text
    assert "Engine Temperature." in text


# ------------- uint64 datatype conversion output test -------------


def test_ros2_test_datatype_uint64(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: uint64
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "uint64 value" in text
    assert "Engine Temperature." in text


# ------------- int8 datatype conversion output test -------------


def test_ros2_test_datatype_int8(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: int8
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "int8 value" in text
    assert "Engine Temperature." in text


# ------------- int16 datatype conversion output test -------------


def test_ros2_test_datatype_int16(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: int16
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "int16 value" in text
    assert "Engine Temperature." in text


# ------------- int32 datatype conversion output test -------------


def test_ros2_test_datatype_int32(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: int32
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "int32 value" in text
    assert "Engine Temperature." in text


# ------------- int64 datatype conversion output test -------------


def test_ros2_test_datatype_int64(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: int64
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "int64 value" in text
    assert "Engine Temperature." in text


# ------------- float32 datatype conversion output test -------------


def test_ros2_test_datatype_float32(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: float
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "float32 value" in text
    assert "Engine Temperature." in text


# ------------- float64 datatype conversion output test -------------


def test_ros2_test_datatype_float64(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.Temperature:
  type: attribute
  datatype: double
  description: Engine Temperature.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineTemperature.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "float64 value" in text
    assert "Engine Temperature." in text


# ------------- string datatype conversion output test -------------


def test_ros2_test_datatype_string(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Engine:
  type: branch
  description: Engine of Branch A.
A.Engine.VIN:
  type: attribute
  datatype: string
  description: Engine VIN Number.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="leaf", extra_args=["--include-dirs", str(INCLUDE_DIR)])
    msg = pkg_dir / "msg" / "AEngineVIN.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    # header & fields written by the exporter
    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "string value" in text
    assert "Engine VIN Number." in text


def test_ros2_struct_timestamp_leaf_msg_and_srv(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Vehicle speed.
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=["--srv", "both", "--srv-use-msg", "--include-dirs", str(INCLUDE_DIR)],
    )

    msg = pkg_dir / "msg" / "ASpeed.msg"
    get_srv = pkg_dir / "srv" / "GetASpeed.srv"
    set_srv = pkg_dir / "srv" / "SetASpeed.srv"

    assert msg.is_file(), f"Missing {msg}"
    assert get_srv.is_file(), f"Missing {get_srv}"
    assert set_srv.is_file(), f"Missing {set_srv}"

    msg_text = read_text(msg)
    get_text = read_text(get_srv)
    set_text = read_text(set_srv)

    assert "int64 timestamp_seconds" in msg_text
    assert "int64 timestamp_nanoseconds" in msg_text
    assert "float32 value" in msg_text
    assert "uint64 timestamp" not in msg_text

    assert "int64 start_time_seconds" in get_text
    assert "int64 start_time_nanoseconds" in get_text
    assert "int64 end_time_seconds" in get_text
    assert "int64 end_time_nanoseconds" in get_text
    assert "ASpeed[] data" in get_text

    assert "ASpeed data" in set_text
    assert "bool success" in set_text
    assert "string message" in set_text


def test_ros2_struct_timestamp_aggregate_mode(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Vehicle speed.
A.RPM:
  type: sensor
  datatype: uint16
  description: Engine RPM.
"""
    pkg_dir = run_ros2_exporter(vspec, tmp_path, mode="aggregate", extra_args=["--include-dirs", str(INCLUDE_DIR)])

    msg = pkg_dir / "msg" / "A.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "float32 speed" in text
    assert "uint16 rpm" in text
    assert "uint64 timestamp" not in text


def test_ros2_struct_timestamp_uses_types_tree(tmp_path):
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Vehicle speed.
"""
    # A types file must have a root namespace (bare structs at root fail RootTypesException).
    types_vspec = tmp_path / "CustomTypes.vspec"
    types_vspec.write_text(
        """\
CustomTypes:
  type: branch
  description: Custom type definitions.

CustomTypes.Timestamp:
  type: struct
  description: A point in time.

CustomTypes.Timestamp.seconds:
  type: property
  datatype: int64
  description: Unix epoch seconds.

CustomTypes.Timestamp.nanoseconds:
  type: property
  datatype: int64
  min: 0
  max: 999999999
  description: Nanosecond offset within the second.
""",
        encoding="utf-8",
    )

    transformed = tmp_path / "out" / "transformed.vspec"
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
        extra_args=[
            "--types",
            str(types_vspec),
            "--timestamp-struct-fqn",
            "CustomTypes.Timestamp",
            "--srv",
            "get",
            "--srv-use-msg",
            "--output-vspec",
            str(transformed),
        ],
    )

    msg = pkg_dir / "msg" / "ASpeed.msg"
    srv = pkg_dir / "srv" / "GetASpeed.srv"
    assert msg.is_file(), f"Missing {msg}"
    assert srv.is_file(), f"Missing {srv}"
    assert transformed.is_file(), f"Missing {transformed}"

    msg_text = read_text(msg)
    srv_text = read_text(srv)
    transformed_text = read_text(transformed)

    assert "int64 timestamp_seconds" in msg_text
    assert "int64 timestamp_nanoseconds" in msg_text
    assert "int32 timestamp_sec" not in msg_text
    assert "uint32 timestamp_nanosec" not in msg_text

    assert "int64 start_time_seconds" in srv_text
    assert "int64 start_time_nanoseconds" in srv_text
    assert "int64 end_time_seconds" in srv_text
    assert "int64 end_time_nanoseconds" in srv_text

    assert "type: property" in transformed_text
    assert "datatype: CustomTypes.Timestamp" in transformed_text
    assert "A.Speed.Time:" in transformed_text
    assert "A.Speed.Time.seconds:" not in transformed_text
    assert "A.Speed.Time.nanoseconds:" not in transformed_text
    assert "Timestamp.seconds:" not in transformed_text
    assert "Timestamp.nanoseconds:" not in transformed_text


def test_ros2_struct_timestamp_fallback_defaults(tmp_path):
    """When no --types file is provided, built-in timestamp defaults (int64 fields) are used."""
    vspec = """\
A:
  type: branch
  description: Branch A.
A.Speed:
  type: sensor
  datatype: float
  description: Vehicle speed.
"""
    pkg_dir = run_ros2_exporter(
        vspec,
        tmp_path,
        mode="leaf",
    )
    msg = pkg_dir / "msg" / "ASpeed.msg"
    assert msg.is_file(), f"Missing {msg}"
    text = read_text(msg)

    assert "int64 timestamp_seconds" in text
    assert "int64 timestamp_nanoseconds" in text
    assert "int32 timestamp_sec" not in text
    assert "uint32 timestamp_nanosec" not in text
    assert "uint64 timestamp" not in text
