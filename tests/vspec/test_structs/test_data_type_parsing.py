#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import os
from pathlib import Path


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


@pytest.mark.parametrize("format, signals_out, expected_signal, type_file", [
    ('json', 'signals-out.json', 'expected-signals-types.json', 'VehicleDataTypes.vspec'),
    ('json', 'signals-out.json', 'expected-signals-types.json', 'VehicleDataTypesFlat.vspec'),
    ('yaml', 'signals-out.yaml', 'expected-signals-types.yaml', 'VehicleDataTypes.vspec'),
    ('csv', 'signals-out.csv', 'expected-signals-types.csv', 'VehicleDataTypes.vspec')])
def test_data_types_export_single_file(format, signals_out, expected_signal, type_file, change_test_dir):
    """
    Test that data types provided in vspec format are converted correctly
    """
    args = ["../../../vspec2" + format + ".py"]
    if format == 'json':
        args.append('--json-pretty')
    args.extend(["-vt", type_file, "-u", "../test_units.yaml",
                 "test.vspec", signals_out, "1>", "out.txt", "2>&1"])
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = f"diff {signals_out} {expected_signal}"
    result = os.system(test_str)
    os.system("rm -f out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    os.system(f"rm -f {signals_out}")


@pytest.mark.parametrize("format,signals_out, data_types_out,expected_signal,expected_data_types", [
    ('json', 'signals-out.json', 'VehicleDataTypes.json', 'expected-signals.json', 'expected.json'),
    ('csv',  'signals-out.csv',  'VehicleDataTypes.csv',  'expected-signals.csv',  'expected.csv'),
    ('yaml',  'signals-out.yaml',  'VehicleDataTypes.yaml',  'expected-signals.yaml',  'expected.yaml')])
def test_data_types_export_multi_file(format, signals_out, data_types_out,
                                      expected_signal, expected_data_types, change_test_dir):
    """
    Test that data types provided in vspec format are converted correctly
    """
    args = ["../../../vspec2" + format + ".py"]
    if format == 'json':
        args.append('--json-pretty')
    args.extend(["-vt", "VehicleDataTypes.vspec", "-u", "../test_units.yaml", "-ot", data_types_out,
                 "test.vspec", signals_out, "1>", "out.txt", "2>&1"])
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = f"diff {data_types_out} {expected_data_types}"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = f"diff {signals_out} {expected_signal}"
    result = os.system(test_str)
    os.system("rm -f out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    os.system(f"rm -f {signals_out} {data_types_out}")


@pytest.mark.parametrize(
        "signal_vspec_file,type_vspec_file,expected_signal_file,actual_signal_file,expected_type_files,"
        "actual_type_files",
        [('test.vspec', 'VehicleDataTypes.vspec', 'ExpectedSignals.proto', 'ActualSignals.proto',
          ['VehicleDataTypes/TestBranch1/ExpectedTestBranch1.proto'],
          ['VehicleDataTypes/TestBranch1/TestBranch1.proto']),
         ('test2.vspec', 'VehicleDataTypes2.vspec', 'ExpectedSignals2.proto', 'ActualSignals.proto',
          ['VehicleDataTypes/TestBranch2/ExpectedTestBranch2.proto',
           'VehicleDataTypes/TestBranch3/ExpectedTestBranch3.proto'],
          ['VehicleDataTypes/TestBranch2/TestBranch2.proto',
           'VehicleDataTypes/TestBranch3/TestBranch3.proto'])])
def test_data_types_export_to_proto(signal_vspec_file, type_vspec_file, expected_signal_file,
                                    actual_signal_file, expected_type_files, actual_type_files,
                                    change_test_dir):
    """
    Test that data types provided in vspec format are converted correctly to protobuf
    """

    data_types_out = Path.cwd() / "unused.proto"
    args = ["../../../vspec2protobuf.py",
            "-vt", type_vspec_file, "-u", "../test_units.yaml",
            "-ot", str(data_types_out), signal_vspec_file, actual_signal_file, "1>", "out.txt", "2>&1"]
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    expected_proto_files = expected_type_files + [expected_signal_file]
    actual_proto_files = actual_type_files + [actual_signal_file]

    os.system("rm -f out.txt")
    for (expected_file, actual_file) in zip(expected_proto_files, actual_proto_files):
        test_str = f"diff {expected_file} {actual_file}"
        result = os.system(test_str)
        assert os.WIFEXITED(result)
        assert os.WEXITSTATUS(result) == 0

    for proto_file in actual_proto_files:
        proto_compile_cmd = f"protoc {proto_file} --cpp_out=. 1>proto.out 2>&1"
        result = os.system(proto_compile_cmd)
        os.system("cat proto.out")
        assert os.WIFEXITED(result)
        assert os.WEXITSTATUS(result) == 0
    # clean up
    for proto_file in actual_proto_files:
        proto_stem = Path(proto_file).stem
        proto_path = Path(os.path.dirname(proto_file))
        os.system(f"rm -f {proto_file} proto.out")
        os.system(f"rm -f {proto_path}/{proto_stem}.pb.cc {proto_path}/{proto_stem}.pb.h")


@pytest.mark.parametrize("types_file,error_msg", [
    ('VehicleDataTypesInvalidStructWithQualifiedName.vspec',
     '2 data type reference errors detected'),
    ('VehicleDataTypesWithCircularRefs.vspec',
     '4 data type reference errors detected'),
    ('VehicleDataTypesInvalidStruct.vspec', 'Data type not found. Data Type: NestedStruct1')])
def test_data_types_invalid_reference_in_data_type_tree(
        types_file, error_msg, change_test_dir):
    """
    Test that errors are surfaced when data type name references are invalid within the data type tree
    """
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml",
                         "--json-pretty", "-vt",
                         types_file, "-ot", "VehicleDataTypes.json", "test.vspec", "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    test_str = f'grep \"{error_msg}\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f VehicleDataTypes.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


@pytest.mark.parametrize("types_file,error_msg", [
    ('VehicleDataTypesInvalidStructWithOrphanProperties.vspec',
     'Orphan property detected. y_property is not defined under a struct')])
def test_data_types_orphan_properties(
        types_file, error_msg, change_test_dir):
    """
    Test that errors are surfaced when a property is not defined under a struct
    """
    test_str = " ".join(["../../../vspec2json.py",  "-u", "../test_units.yaml",
                         "--json-pretty", "-vt",
                         types_file, "-ot", "VehicleDataTypes.json", "test.vspec", "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    test_str = f'grep \"{error_msg}\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system('cat out.txt')
    os.system("rm -f VehicleDataTypes.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_data_types_invalid_reference_in_signal_tree(change_test_dir):
    """
    Test that errors are surfaced when data type name references are invalid in the signal tree
    """
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml",
                         "--json-pretty", "-vt",
                         "VehicleDataTypes.vspec", "-ot", "VehicleDataTypes.json", "test-invalid-datatypes.vspec",
                         "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    error_msg = ('Following types were referenced in signals but have not been defined: '
                 'VehicleDataTypes.TestBranch1.ParentStruct1, VehicleDataTypes.TestBranch1.NestedStruct1')
    test_str = f'grep \"{error_msg}\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f VehicleDataTypes.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_error_when_no_user_defined_data_types_are_provided(change_test_dir):
    """
    Test that error message is provided when user-defined types are specified
    in the signal tree but no data type tree is provided.
    """
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml",
                         "--json-pretty", "test.vspec", "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    error_msg = ('Following types were referenced in signals but have not been defined: '
                 'VehicleDataTypes.TestBranch1.ParentStruct, VehicleDataTypes.TestBranch1.NestedStruct')
    test_str = f'grep \"{error_msg}\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f VehicleDataTypes.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


@pytest.mark.parametrize("vspec_file,types_file,error_msg", [
    ('test.vspec', 'VehicleDataTypesStructWithDataType.vspec',
     'cannot have datatype, only allowed for signal and property'),
    ('test.vspec', 'VehicleDataTypesStructWithUnit.vspec',
     'cannot have unit'),
    ('test_with_unit_on_struct_signal.vspec', 'VehicleDataTypes.vspec',
     'Unit specified for item not using standard datatype')])
def test_faulty_use_of_standard_attributes(
        vspec_file, types_file, error_msg, change_test_dir):
    """
    Test faulty use of datatype and unit for structs
    """
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml",
                         "--json-pretty", "-vt", types_file, "-ot", "VehicleDataTypes.json", vspec_file,
                         "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    test_str = f'grep \"{error_msg}\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f VehicleDataTypes.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
