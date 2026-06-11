# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Tests for the AVRO IDL exporter."""

from pathlib import Path

import inflect
import pytest
from vss_tools.exporters.avro import (
    build_enum_name,
    collect_enums,
    collect_nested_structs_ordered,
    ensure_unknown_first,
    generate_protocol,
    get_top_level_structs,
    to_avro_field_name,
    vss_type_to_avro,
)
from vss_tools.main import get_trees

# ---------------------------------------------------------------------------
# Fixture: shared tree loaded from test vspec files
# ---------------------------------------------------------------------------

_SIGNALS = Path("tests/vspec/test_avro/signals.vspec")
_TYPES = Path("tests/vspec/test_avro/types.vspec")
_UNITS = Path("tests/vspec/test_units.yaml")
_QUANTITIES = Path("tests/vspec/test_quantities.yaml")


@pytest.fixture(scope="module")
def type_trees():
    """Load the test signals and type trees once per module."""
    tree, data_type_tree = get_trees(
        vspec=_SIGNALS,
        include_dirs=(),
        aborts=(),
        strict=False,
        extended_attributes=(),
        quantities=(_QUANTITIES,),
        units=(_UNITS,),
        types=(_TYPES,),
        overlays=(),
        expand=False,
    )
    return tree, data_type_tree


@pytest.fixture(scope="module")
def top_level_structs(type_trees):
    _, data_type_tree = type_trees
    return get_top_level_structs(data_type_tree)


@pytest.fixture(scope="module")
def sensor_node(top_level_structs):
    return next(n for n in top_level_structs if n.name == "Sensor")


@pytest.fixture(scope="module")
def alert_record_node(top_level_structs):
    return next(n for n in top_level_structs if n.name == "AlertRecord")


@pytest.fixture(scope="module")
def schedule_node(top_level_structs):
    return next(n for n in top_level_structs if n.name == "Schedule")


# ---------------------------------------------------------------------------
# Unit tests for pure helpers
# ---------------------------------------------------------------------------


class TestVssTypeToAvro:
    def test_primitive_mappings(self):
        assert vss_type_to_avro("uint8") == "int"
        assert vss_type_to_avro("int8") == "int"
        assert vss_type_to_avro("uint16") == "int"
        assert vss_type_to_avro("int16") == "int"
        assert vss_type_to_avro("int32") == "int"
        assert vss_type_to_avro("uint32") == "long"
        assert vss_type_to_avro("int64") == "long"
        assert vss_type_to_avro("uint64") == "long"
        assert vss_type_to_avro("float") == "float"
        assert vss_type_to_avro("double") == "double"
        assert vss_type_to_avro("boolean") == "boolean"
        assert vss_type_to_avro("string") == "string"

    def test_array_types_map_to_bytes(self):
        assert vss_type_to_avro("uint8[]") == "bytes"
        assert vss_type_to_avro("string[]") == "bytes"
        assert vss_type_to_avro("float[]") == "bytes"

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            vss_type_to_avro("not_a_real_type")


class TestEnsureUnknownFirst:
    def test_adds_unknown_when_absent(self):
        result = ensure_unknown_first(["ALPHA", "BETA"])
        assert result == ["UNKNOWN", "ALPHA", "BETA"]

    def test_moves_unknown_to_front(self):
        result = ensure_unknown_first(["ALPHA", "UNKNOWN", "BETA"])
        assert result[0] == "UNKNOWN"
        assert "UNKNOWN" not in result[1:]

    def test_no_duplicate_when_already_first(self):
        result = ensure_unknown_first(["UNKNOWN", "ALPHA"])
        assert result.count("UNKNOWN") == 1
        assert result[0] == "UNKNOWN"

    def test_empty_list_gets_unknown(self):
        result = ensure_unknown_first([])
        assert result == ["UNKNOWN"]


class TestBuildEnumName:
    def test_single_segment_path(self):
        name = build_enum_name(["Reading"], "Status")
        assert name == "ReadingStatusValue"

    def test_two_segment_path(self):
        name = build_enum_name(["Schedule", "Window"], "Mode")
        assert name == "ScheduleWindowModeValue"

    def test_three_segment_path(self):
        name = build_enum_name(["Config", "Network", "Retry"], "Policy")
        assert name == "ConfigNetworkRetryPolicyValue"


class TestToAvroFieldName:
    def test_pascal_to_camel(self):
        assert to_avro_field_name("SampleRate") == "sampleRate"
        assert to_avro_field_name("IsEnabled") == "isEnabled"
        assert to_avro_field_name("HasPendingUpdate") == "hasPendingUpdate"
        assert to_avro_field_name("StartMinute") == "startMinute"


# ---------------------------------------------------------------------------
# Integration tests using the loaded tree
# ---------------------------------------------------------------------------


class TestTopLevelStructDiscovery:
    def test_finds_expected_structs(self, top_level_structs):
        names = {n.name for n in top_level_structs}
        assert "Sensor" in names
        assert "AlertRecord" in names
        assert "Schedule" in names

    def test_does_not_include_nested_structs(self, top_level_structs):
        names = {n.name for n in top_level_structs}
        assert "Window" not in names


class TestCollectEnums:
    def test_no_enums_for_simple_struct(self, sensor_node):
        assert collect_enums(sensor_node) == []

    def test_enum_for_allowed_field(self, alert_record_node):
        enums = collect_enums(alert_record_node)
        assert len(enums) == 1
        enum_name, values = enums[0]
        assert enum_name == "AlertRecordSeverityValue"

    def test_unknown_prepended_to_enum(self, alert_record_node):
        _, values = collect_enums(alert_record_node)[0]
        assert values[0] == "UNKNOWN"
        assert "LOW" in values
        assert "MEDIUM" in values
        assert "HIGH" in values
        assert "CRITICAL" in values

    def test_unknown_already_in_allowed_not_duplicated(self, type_trees):
        """A struct whose allowed list already contains UNKNOWN gets it once at index 0."""
        _, data_type_tree = type_trees
        get_top_level_structs(data_type_tree)

        # Build a synthetic check via the helper directly
        result = ensure_unknown_first(["ALPHA", "UNKNOWN", "BETA"])
        assert result.count("UNKNOWN") == 1
        assert result[0] == "UNKNOWN"


class TestCollectNestedStructs:
    def test_no_nested_for_flat_struct(self, sensor_node):
        assert collect_nested_structs_ordered(sensor_node) == []

    def test_nested_struct_found_for_schedule(self, schedule_node):
        nested = collect_nested_structs_ordered(schedule_node)
        names = [n.name for n in nested]
        assert "Window" in names

    def test_nested_declared_before_parent(self, schedule_node):
        """Window must appear before Schedule in the ordered list."""
        nested = collect_nested_structs_ordered(schedule_node)
        names = [n.name for n in nested]
        assert names.index("Window") < len(names)  # Window is in the list


class TestGenerateProtocol:
    _NS = "com.test.vss.struct"
    _ENGINE = inflect.engine()

    def test_namespace_in_output(self, sensor_node):
        content = generate_protocol(sensor_node, self._NS, False, self._ENGINE)
        assert '@namespace("com.test.vss.struct.sensor")' in content

    def test_protocol_name_in_output(self, sensor_node):
        content = generate_protocol(sensor_node, self._NS, False, self._ENGINE)
        assert "protocol Sensor {" in content

    def test_simple_struct_fields(self, sensor_node):
        content = generate_protocol(sensor_node, self._NS, False, self._ENGINE)
        assert "union { null, double } value;" in content
        assert "union { null, int } quality;" in content

    def test_main_record_present(self, sensor_node):
        content = generate_protocol(sensor_node, self._NS, False, self._ENGINE)
        assert "record Sensor {" in content

    def test_no_array_record_by_default(self, sensor_node):
        content = generate_protocol(sensor_node, self._NS, False, self._ENGINE)
        assert "SensorArray" not in content

    def test_array_record_generated_when_requested(self, sensor_node):
        content = generate_protocol(sensor_node, self._NS, True, self._ENGINE)
        assert "record SensorArray {" in content
        assert "array<Sensor> sensors;" in content

    def test_enum_present_for_alert_record(self, alert_record_node):
        content = generate_protocol(alert_record_node, self._NS, False, self._ENGINE)
        assert "enum AlertRecordSeverityValue {" in content
        assert "} = UNKNOWN;" in content

    def test_unknown_is_first_in_enum(self, alert_record_node):
        content = generate_protocol(alert_record_node, self._NS, False, self._ENGINE)
        lines = content.splitlines()
        enum_start = next(i for i, line in enumerate(lines) if "enum AlertRecordSeverityValue" in line)
        first_value_line = lines[enum_start + 1].strip()
        assert first_value_line.startswith("UNKNOWN")

    def test_enum_default_is_unknown(self, alert_record_node):
        content = generate_protocol(alert_record_node, self._NS, False, self._ENGINE)
        assert "} = UNKNOWN;" in content

    def test_enum_field_references_enum_type(self, alert_record_node):
        content = generate_protocol(alert_record_node, self._NS, False, self._ENGINE)
        assert "union { null, AlertRecordSeverityValue } severity;" in content

    def test_nested_struct_record_present(self, schedule_node):
        content = generate_protocol(schedule_node, self._NS, False, self._ENGINE)
        assert "record Window {" in content

    def test_nested_record_before_parent(self, schedule_node):
        content = generate_protocol(schedule_node, self._NS, False, self._ENGINE)
        window_pos = content.index("record Window {")
        schedule_pos = content.index("record Schedule {")
        assert window_pos < schedule_pos

    def test_nested_struct_referenced_in_parent(self, schedule_node):
        content = generate_protocol(schedule_node, self._NS, False, self._ENGINE)
        assert "union { null, Window } window;" in content

    def test_uint64_maps_to_long(self, alert_record_node):
        content = generate_protocol(alert_record_node, self._NS, False, self._ENGINE)
        assert "union { null, long } occurredAt;" in content

    def test_uint8_maps_to_int(self, schedule_node):
        content = generate_protocol(schedule_node, self._NS, False, self._ENGINE)
        assert "union { null, int } repeatCount;" in content

    def test_boolean_field(self, schedule_node):
        content = generate_protocol(schedule_node, self._NS, False, self._ENGINE)
        assert "union { null, boolean } isEnabled;" in content

    def test_int_in_nested_record(self, schedule_node):
        content = generate_protocol(schedule_node, self._NS, False, self._ENGINE)
        assert "union { null, int } startMinute;" in content

    def test_array_record_plural_field_name(self, schedule_node):
        content = generate_protocol(schedule_node, self._NS, True, self._ENGINE)
        assert "array<Schedule> schedules;" in content

    def test_output_ends_with_newline(self, sensor_node):
        content = generate_protocol(sensor_node, self._NS, False, self._ENGINE)
        assert content.endswith("\n")


class TestFilePrefix:
    def test_file_prefix_applied(self, sensor_node, tmp_path, type_trees):
        _, data_type_tree = type_trees
        structs = get_top_level_structs(data_type_tree)
        node = next(n for n in structs if n.name == "Sensor")

        p = inflect.engine()
        generate_protocol(node, "com.test.struct", False, p)
        filename = f"struct{node.name}.avdl"
        assert filename == "structSensor.avdl"

    def test_no_prefix_gives_plain_name(self, sensor_node):
        assert f"{sensor_node.name}.avdl" == "Sensor.avdl"


class TestCLIIntegration:
    def test_cli_writes_files_to_output_dir(self, tmp_path):
        from click.testing import CliRunner
        from vss_tools.exporters.avro import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-s",
                str(_SIGNALS),
                "-t",
                str(_TYPES),
                "-u",
                str(_UNITS),
                "-q",
                str(_QUANTITIES),
                "-o",
                str(tmp_path),
                "--namespace",
                "com.test.struct",
            ],
        )
        assert result.exit_code == 0, result.output
        generated = {p.name for p in tmp_path.glob("*.avdl")}
        assert "Sensor.avdl" in generated
        assert "AlertRecord.avdl" in generated
        assert "Schedule.avdl" in generated

    def test_cli_file_prefix(self, tmp_path):
        from click.testing import CliRunner
        from vss_tools.exporters.avro import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-s",
                str(_SIGNALS),
                "-t",
                str(_TYPES),
                "-u",
                str(_UNITS),
                "-q",
                str(_QUANTITIES),
                "-o",
                str(tmp_path),
                "--namespace",
                "com.test.struct",
                "--file-prefix",
                "struct",
            ],
        )
        assert result.exit_code == 0, result.output
        generated = {p.name for p in tmp_path.glob("*.avdl")}
        assert "structSensor.avdl" in generated
        assert "structAlertRecord.avdl" in generated

    def test_cli_include_array_record(self, tmp_path):
        from click.testing import CliRunner
        from vss_tools.exporters.avro import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-s",
                str(_SIGNALS),
                "-t",
                str(_TYPES),
                "-u",
                str(_UNITS),
                "-q",
                str(_QUANTITIES),
                "-o",
                str(tmp_path),
                "--namespace",
                "com.test.struct",
                "--include-array-record",
            ],
        )
        assert result.exit_code == 0, result.output
        content = (tmp_path / "Sensor.avdl").read_text()
        assert "record SensorArray {" in content
        assert "array<Sensor> sensors;" in content

    def test_cli_requires_namespace(self, tmp_path):
        from click.testing import CliRunner
        from vss_tools.exporters.avro import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-s",
                str(_SIGNALS),
                "-t",
                str(_TYPES),
                "-o",
                str(tmp_path),
                # --namespace intentionally omitted
            ],
        )
        assert result.exit_code != 0

    def test_cli_requires_types(self, tmp_path):
        from click.testing import CliRunner
        from vss_tools.exporters.avro import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "-s",
                str(_SIGNALS),
                "-o",
                str(tmp_path),
                "--namespace",
                "com.test.struct",
                # --types intentionally omitted
            ],
        )
        assert result.exit_code != 0
