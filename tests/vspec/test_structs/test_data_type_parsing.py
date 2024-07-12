# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import os
import filecmp
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VSS_TOOLS_ROOT = (HERE / ".." / ".." / "..").absolute()
TEST_UNITS = HERE / ".." / "test_units.yaml"


@pytest.mark.parametrize(
    "format, signals_out, expected_signal, type_file",
    [
        (
            "json",
            "signals-out.json",
            "expected-signals-types.json",
            "VehicleDataTypes.vspec",
        ),
        (
            "json",
            "signals-out.json",
            "expected-signals-types.json",
            "VehicleDataTypesFlat.vspec",
        ),
        (
            "yaml",
            "signals-out.yaml",
            "expected-signals-types.yaml",
            "VehicleDataTypes.vspec",
        ),
        (
            "csv",
            "signals-out.csv",
            "expected-signals-types.csv",
            "VehicleDataTypes.vspec",
        ),
        (
            "ddsidl",
            "signals-out.idl",
            "expected-signals-types.idl",
            "VehicleDataTypes.vspec",
        ),
    ],
)
def test_data_types_export_single_file(
    format, signals_out, expected_signal, type_file, tmp_path
):
    """
    Test that data types provided in vspec format are converted correctly
    """
    type_file = HERE / type_file
    vspec = HERE / "test.vspec"
    output = tmp_path / signals_out
    cmd = f"vspec2x {format}"
    if format == "json":
        cmd += " --pretty"
    cmd += f" --types {type_file} -u {TEST_UNITS} --vspec {vspec} --output {output}"
    subprocess.run(cmd.split(), check=True)
    expected_output = HERE / expected_signal
    assert filecmp.cmp(output, expected_output)


@pytest.mark.parametrize(
    "format,signals_out, data_types_out,expected_signal,expected_data_types",
    [
        (
            "json",
            "signals-out.json",
            "VehicleDataTypes.json",
            "expected-signals.json",
            "expected.json",
        ),
        (
            "csv",
            "signals-out.csv",
            "VehicleDataTypes.csv",
            "expected-signals.csv",
            "expected.csv",
        ),
        (
            "yaml",
            "signals-out.yaml",
            "VehicleDataTypes.yaml",
            "expected-signals.yaml",
            "expected.yaml",
        ),
    ],
)
def test_data_types_export_multi_file(
    format,
    signals_out,
    data_types_out,
    expected_signal,
    expected_data_types,
    tmp_path,
):
    """
    Test that data types provided in vspec format are converted correctly
    Note that DDSIDL does not support -ot
    """

    type_file = HERE / "VehicleDataTypes.vspec"
    vspec = HERE / "test.vspec"
    output = tmp_path / signals_out
    types_output = tmp_path / data_types_out
    cmd = f"vspec2x {format}"
    if format == "json":
        cmd += " --pretty"
    cmd += f" --types {type_file} -u {TEST_UNITS} --types-output {types_output} --vspec {vspec} --output {output}"
    subprocess.run(cmd.split(), check=True)
    expected_signal = HERE / expected_signal
    expected_data_types = HERE / expected_data_types
    assert filecmp.cmp(output, expected_signal)
    assert filecmp.cmp(types_output, expected_data_types)


@pytest.mark.parametrize(
    "signal_vspec_file,type_vspec_file,expected_signal_file,actual_signal_file,expected_type_files,"
    "actual_type_files",
    [
        (
            "test.vspec",
            "VehicleDataTypes.vspec",
            "ExpectedSignals.proto",
            "ActualSignals.proto",
            ["VehicleDataTypes/TestBranch1/ExpectedTestBranch1.proto"],
            ["VehicleDataTypes/TestBranch1/TestBranch1.proto"],
        ),
        (
            "test2.vspec",
            "VehicleDataTypes2.vspec",
            "ExpectedSignals2.proto",
            "ActualSignals.proto",
            [
                "VehicleDataTypes/TestBranch2/ExpectedTestBranch2.proto",
                "VehicleDataTypes/TestBranch3/ExpectedTestBranch3.proto",
            ],
            [
                "VehicleDataTypes/TestBranch2/TestBranch2.proto",
                "VehicleDataTypes/TestBranch3/TestBranch3.proto",
            ],
        ),
    ],
)
def test_data_types_export_to_proto(
    signal_vspec_file,
    type_vspec_file,
    expected_signal_file,
    actual_signal_file,
    expected_type_files,
    actual_type_files,
    tmp_path,
):
    """
    Test that data types provided in vspec format are converted correctly to protobuf
    """
    signal_vspec_file = HERE / signal_vspec_file
    type_vspec_file = HERE / type_vspec_file
    expected_signal_file = HERE / expected_signal_file
    expected_type_files = [HERE / f for f in expected_type_files]
    actual_signal_file = tmp_path / actual_signal_file
    actual_type_files = [tmp_path / f for f in actual_type_files]
    data_types_out = tmp_path

    cmd = (
        f"vspec2x protobuf --types {type_vspec_file} -u {TEST_UNITS} --types-out-dir {data_types_out}"
        f" --vspec {signal_vspec_file} --output {actual_signal_file}"
    )

    subprocess.run(cmd.split(), cwd=tmp_path, check=True)

    expected_proto_files = expected_type_files + [expected_signal_file]
    actual_proto_files = actual_type_files + [actual_signal_file]

    for expected_file, actual_file in zip(expected_proto_files, actual_proto_files):
        assert filecmp.cmp(expected_file, actual_file)

    for proto_file in actual_proto_files:
        proto_compile_cmd = f"protoc {proto_file} --cpp_out=. -I {tmp_path}"
        process = subprocess.run(proto_compile_cmd.split(), cwd=tmp_path)
        assert process.returncode == 0


@pytest.mark.parametrize(
    "types_file,error_msg",
    [
        (
            "VehicleDataTypesInvalidStructWithQualifiedName.vspec",
            "2 data type reference errors detected",
        ),
        (
            "VehicleDataTypesWithCircularRefs.vspec",
            "4 data type reference errors detected",
        ),
        (
            "VehicleDataTypesInvalidStruct.vspec",
            "Data type not found. Data Type: NestedStruct1",
        ),
    ],
)
def test_data_types_invalid_reference_in_data_type_tree(
    types_file, error_msg, tmp_path
):
    """
    Test that errors are surfaced when data type name references are invalid within the data type tree
    """
    types_file = HERE / types_file
    output_types = tmp_path / "VehicleDataTypes.vspec"
    vspec = HERE / "test.vspec"
    output = tmp_path / "out.json"
    cmd = f"vspec2x json -u {TEST_UNITS} --pretty --types {types_file} --types-output {output_types} --vspec {vspec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert error_msg in process.stdout


@pytest.mark.parametrize(
    "types_file,error_msg",
    [
        (
            "VehicleDataTypesInvalidStructWithOrphanProperties.vspec",
            "Orphan property detected. y_property is not defined under a struct",
        )
    ],
)
def test_data_types_orphan_properties(types_file, error_msg, tmp_path):
    """
    Test that errors are surfaced when a property is not defined under a struct
    """
    types_file = HERE / types_file
    types_out = tmp_path / "VehicleDataTypes.vspec"
    vspec = HERE / "test.vspec"
    out = tmp_path / "out.json"

    cmd = f"vspec2x json -u {TEST_UNITS} --pretty --types {types_file} --types-output {types_out} --vspec {vspec} --output {out}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0
    assert error_msg in process.stdout


def test_data_types_invalid_reference_in_signal_tree(tmp_path):
    """
    Test that errors are surfaced when data type name references are invalid in the signal tree
    """
    types_file = HERE / "VehicleDataTypes.vspec"
    types_out = tmp_path / "VehicleDataTypes.json"
    vspec = HERE / "test-invalid-datatypes.vspec"
    out = tmp_path / "out.json"

    cmd = f"vspec2x json -u {TEST_UNITS} --pretty --types {types_file} --types-output {types_out} --vspec {vspec} --output {out}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0

    error_msg = (
        "Following types were referenced in signals but have not been defined: "
        "VehicleDataTypes.TestBranch1.ParentStruct1, VehicleDataTypes.TestBranch1.NestedStruct1"
    )
    assert error_msg in process.stdout


def test_error_when_no_user_defined_data_types_are_provided(tmp_path):
    """
    Test that error message is provided when user-defined types are specified
    in the signal tree but no data type tree is provided.
    """
    vspec = HERE / "test.vspec"
    out = tmp_path / "out.json"
    cmd = f"vspec2x json -u {TEST_UNITS} --pretty --vspec {vspec} --output {out}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0

    error_msg = (
        "Following types were referenced in signals but have not been defined: "
        "VehicleDataTypes.TestBranch1.ParentStruct, VehicleDataTypes.TestBranch1.NestedStruct"
    )
    assert error_msg in process.stdout


@pytest.mark.parametrize(
    "vspec_file,types_file,error_msg",
    [
        (
            "test.vspec",
            "VehicleDataTypesStructWithDataType.vspec",
            "cannot have datatype, only allowed for signal and property",
        ),
        ("test.vspec", "VehicleDataTypesStructWithUnit.vspec", "cannot have unit"),
        (
            "test_with_unit_on_struct_signal.vspec",
            "VehicleDataTypes.vspec",
            "Unit specified for item not using standard datatype",
        ),
    ],
)
def test_faulty_use_of_standard_attributes(vspec_file, types_file, error_msg, tmp_path):
    """
    Test faulty use of datatype and unit for structs
    """
    types_file = HERE / types_file
    types_out = tmp_path / "VehicleDataTypes.json"
    vspec_file = HERE / vspec_file
    out = tmp_path / "out.json"

    cmd = f"vspec2x json -u {TEST_UNITS} --pretty --types {types_file} --types-output {types_out} --vspec {vspec_file} --output {out}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0
    assert error_msg in process.stdout
