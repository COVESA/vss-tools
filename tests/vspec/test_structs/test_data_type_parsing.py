# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import filecmp
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
VSS_TOOLS_ROOT = (HERE / ".." / ".." / "..").absolute()
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


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
        (
            "apigear",
            "signals-out.apigear",
            "expected-signals-types.apigear",
            "VehicleDataTypes.vspec",
        ),
    ],
)
def test_data_types_export_single_file(format, signals_out, expected_signal, type_file, tmp_path):
    """
    Test that data types provided in vspec format are converted correctly
    """
    type_file = HERE / type_file
    vspec = HERE / "test.vspec"
    output = tmp_path / signals_out
    cmd = f"vspec export {format}"
    if format == "json":
        cmd += " --pretty"
    cmd += f" --types {type_file} -u {TEST_UNITS} -q {TEST_QUANT} --vspec {vspec} "
    if format == "apigear":
        cmd += f"--output-dir {output}"
    else:
        cmd += f"--output {output}"
    subprocess.run(cmd.split(), check=True)
    expected_output = HERE / expected_signal
    if format == "apigear":
        dcmp = filecmp.dircmp(output, expected_output)
        assert not (dcmp.diff_files or dcmp.left_only or dcmp.right_only)
    else:
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
    cmd = f"vspec export {format}"
    if format == "json":
        cmd += " --pretty"
    cmd += f" --types {type_file} -u {TEST_UNITS} -q {TEST_QUANT} --types-output {types_output}"
    cmd += f" --vspec {vspec} --output {output}"
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
        f"vspec export protobuf --types {type_vspec_file} -u {TEST_UNITS} -q {TEST_QUANT}"
        f" --types-out-dir {data_types_out}"
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
            "'VehicleDataTypes.NestedStruct1' is not a valid datatype",
        ),
        (
            "VehicleDataTypesWithCircularRefs.vspec",
            "'ParentStruct' is not a valid datatype",
        ),
        (
            "VehicleDataTypesInvalidStruct.vspec",
            "'NestedStruct1' is not a valid datatype",
        ),
    ],
)
def test_data_types_invalid_reference_in_data_type_tree(types_file, error_msg, tmp_path):
    """
    Test that errors are surfaced when data type name references are invalid within the data type tree
    """
    types_file = HERE / types_file
    output_types = tmp_path / "VehicleDataTypes.vspec"
    vspec = HERE / "test.vspec"
    output = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json -u {TEST_UNITS} -q {TEST_QUANT} --pretty --types {types_file}"
    cmd += f" --types-output {output_types} --vspec {vspec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert error_msg in log.read_text()


@pytest.mark.parametrize(
    "types_file,error_msg",
    [
        (
            "VehicleDataTypesInvalidStructWithOrphanProperties.vspec",
            "invalid parent: 'VSSDataBranch'",
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
    log = tmp_path / "log.txt"

    cmd = f"vspec --log-file {log} export json -u {TEST_UNITS} -q {TEST_QUANT} --pretty --types {types_file}"
    cmd += f" --types-output {types_out} --vspec {vspec} --output {out}"
    process = subprocess.run(cmd.split())
    assert process.returncode != 0
    assert error_msg in log.read_text()


def test_data_types_invalid_reference_in_signal_tree(tmp_path):
    """
    Test that errors are surfaced when data type name references are invalid in the signal tree
    """
    types_file = HERE / "VehicleDataTypes.vspec"
    types_out = tmp_path / "VehicleDataTypes.json"
    vspec = HERE / "test-invalid-datatypes.vspec"
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"

    cmd = f"vspec --log-file {log} export json -u {TEST_UNITS} -q {TEST_QUANT} --pretty --types {types_file}"
    cmd += f" --types-output {types_out} --vspec {vspec} --output {out}"
    process = subprocess.run(cmd.split())
    assert process.returncode != 0

    error_msg = "'VehicleDataTypes.TestBranch1.ParentStruct1' is not a valid datatype"
    assert error_msg in log.read_text()


def test_error_when_no_user_defined_data_types_are_provided(tmp_path):
    """
    Test that error message is provided when user-defined types are specified
    in the signal tree but no data type tree is provided.
    """
    vspec = HERE / "test.vspec"
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json -u {TEST_UNITS} -q {TEST_QUANT} --pretty --vspec {vspec} --output {out}"
    process = subprocess.run(cmd.split())
    assert process.returncode != 0

    error_msg = "'VehicleDataTypes.TestBranch1.ParentStruct' is not a valid datatype"
    assert error_msg in log.read_text()


@pytest.mark.parametrize(
    "vspec_file,types_file,error_msg",
    [
        (
            "test.vspec",
            "VehicleDataTypesStructWithDataType.vspec",
            "Unknown extra attribute: 'VehicleDataTypes.TestBranch1.NestedStruct':'datatype'",
        ),
        (
            "test.vspec",
            "VehicleDataTypesStructWithUnit.vspec",
            "Unknown extra attribute: 'VehicleDataTypes.TestBranch1.NestedStruct':'unit'",
        ),
        (
            "test_with_unit_on_struct_signal.vspec",
            "VehicleDataTypes.vspec",
            "Cannot use 'unit' with struct datatype: 'VehicleDataTypes.TestBranch1.ParentStruct'",
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
    log = tmp_path / "log.txt"

    cmd = f"vspec --log-file {log} export json -u {TEST_UNITS} -q {TEST_QUANT} --pretty --types {types_file}"
    cmd += f" --types-output {types_out} --vspec {vspec_file} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert error_msg in log.read_text() or error_msg in process.stderr


def test_data_types_for_multiple_apigear_templates(tmp_path):
    """
    Test that data types are converted for every ApiGear template
    """
    types_file = HERE / "VehicleDataTypes.vspec"
    vspec = HERE / "test.vspec"
    out = tmp_path / "out.apigear"
    cmd = f"vspec export apigear -u {TEST_UNITS} -q {TEST_QUANT} --types {types_file}"
    cmd += f" --vspec {vspec} --output-dir {out}"
    cmd += " --apigear-template-unreal-path unreal_path"
    cmd += " --apigear-template-cpp-path cpp14_path"
    cmd += " --apigear-template-qt5-path qt5_path"
    cmd += " --apigear-template-qt6-path qt6_path"
    subprocess.run(cmd.split(), check=True)
    expected_output = HERE / "out.apigear"
    dcmp = filecmp.dircmp(out, expected_output)
    assert not (dcmp.diff_files or dcmp.left_only or dcmp.right_only)
