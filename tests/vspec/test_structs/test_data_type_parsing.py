#!/usr/bin/env python3

# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import pytest
import os


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


@pytest.mark.parametrize("format,signals_out, data_types_out,expected_signal,expected_data_types", [
    ('json', 'signals-out.json', 'VehicleDataTypes.json', 'expected-signals.json', 'expected.json'),
    ('csv',  'signals-out.csv',  'VehicleDataTypes.csv',  'expected-signals.csv',  'expected.csv'),
    ('yaml',  'signals-out.yaml',  'VehicleDataTypes.yaml',  'expected-signals.yaml',  'expected.yaml')])
def test_data_types_export(format, signals_out, data_types_out, expected_signal, expected_data_types, change_test_dir):
    """
    Test that data types provided in vspec format are converted correctly
    """
    test_str = " ".join(["../../../vspec2json.py", "--no-uuid", "--format", "json",
                         "--json-pretty", "-vt", "VehicleDataTypes.vspec", "-u", "../test_units.yaml", "-ot",
                         "VehicleDataTypes.json", "test.vspec", "out.json", "1>",
                         "out.txt", "2>&1"])
    result = os.system(test_str)
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


@pytest.mark.parametrize("types_file,error_msg", [
    ('VehicleDataTypesInvalidStructWithQualifiedName.vspec',
     '2 data type reference errors detected'),
    ('VehicleDataTypesInvalidStruct.vspec', 'Data type not found. Data Type: NestedStruct1')])
def test_data_types_invalid_reference_in_data_type_tree(
        types_file, error_msg, change_test_dir):
    """
    Test that errors are surfaced when data type name references are invalid within the data type tree
    """
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml", "--no-uuid", "--format", "json",
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
    test_str = " ".join(["../../../vspec2json.py",  "-u", "../test_units.yaml", "--no-uuid", "--format", "json",
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
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml", "--no-uuid", "--format", "json",
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
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml", "--no-uuid", "--format", "json",
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


def test_warning_when_data_type_is_provided_for_struct_nodes(change_test_dir):
    """
    Test that warning message is provided when datatype is specified for struct nodes.
    """
    test_str = " ".join(["../../../vspec2json.py", "-u", "../test_units.yaml", "--no-uuid", "--format", "json",
                         "--json-pretty", "-vt",
                         "VehicleDataTypesStructWithDataType.vspec", "-ot", "VehicleDataTypes.json", "test.vspec",
                         "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    error_msg = 'Data type specified for struct node: NestedStruct. Ignoring it'
    test_str = f'grep \"{error_msg}\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f VehicleDataTypes.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
