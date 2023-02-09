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


def test_data_types_export_to_json(change_test_dir):
    """
    Test that data types provided in vspec format are converted correctly to the JSON format
    """
    test_str = " ".join(["../../../vspec2json.py", "--no-uuid", "--format", "json", "--json-pretty", "-vt",
                        "VehicleDataTypes.vspec", "-ot", "VehicleDataTypes.json", "test.vspec", "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff VehicleDataTypes.json expected.json"
    result = os.system(test_str)
    os.system("rm -f VehicleDataTypes.json")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff out.json expected-signals.json"
    result = os.system(test_str)
    os.system("rm -f out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


@pytest.mark.parametrize("types_file,error_msg", [
    ('VehicleDataTypesInvalidStructWithQualifiedName.vspec',
     '2 data type reference errors detected'),
    ('VehicleDataTypesInvalidStruct.vspec', 'Data type not found. Data Type: NestedStruct1')])
def test_data_types_invalid_reference_in_data_type_tree(
        types_file, error_msg, change_test_dir):
    """
    Test that errors are surfaced when data type name references are invalid within the data type tree
    """
    test_str = " ".join(["../../../vspec2json.py", "--no-uuid", "--format", "json", "--json-pretty", "-vt",
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


def test_data_types_invalid_reference_in_signal_tree(change_test_dir):
    """
    Test that errors are surfaced when data type name references are invalid in the signal tree
    """
    test_str = " ".join(["../../../vspec2json.py", "--no-uuid", "--format", "json", "--json-pretty", "-vt",
                        "VehicleDataTypes.vspec", "-ot", "VehicleDataTypes.json", "test-invalid-datatypes.vspec", "out.json", "1>", "out.txt", "2>&1"])
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    error_msg = 'Following types were referenced in signals but have not been defined: VehicleDataTypes.TestBranch1.ParentStruct1, VehicleDataTypes.TestBranch1.NestedStruct1'
    test_str = f'grep \"{error_msg}\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f VehicleDataTypes.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
