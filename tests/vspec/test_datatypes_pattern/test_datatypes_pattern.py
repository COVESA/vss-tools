# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


# TODO-Kosta:
#       Test that:
#
#           FAILS when other than string and string[] datatypes have defined pattern
#
#           FAILS when pattern is defined and default is defined and default value does not match pattern
#               - there should be test for default and allowed values,
#                 where allowed is mainly for string[] datatypes
#
#       Add above three fail tests and 1 success test


def test_datatype_pattern_wrong_type(tmp_path):
    spec = HERE / "test_pattern_wrong_datatype.vspec"
    output = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = (
        f"vspec --log-file {log} export json --pretty -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    )
    process = subprocess.run(cmd.split())
    assert process.returncode != 0

    print(process.stdout)
    assert "Field 'pattern' is not allowed for type: 'uint16'. Allowed types: ['string', 'string[]']" in log.read_text()


def test_datatype_pattern_no_match(tmp_path):
    def get_log_msg(value_type: str, value: str):
        return f"Specified '{value_type}' value: '{value}' must match defined pattern: '^[a-z]+$'"

    no_pattern_match_tests_to_run = {
        # Test #1: test no match of defined DEFAULT value
        "test_pattern_no_default_match.vspec": get_log_msg("default", "WrongLabel1"),
        # Test #2: test no match of defined DEFAULT list of values
        "test_pattern_no_default_array_match.vspec": get_log_msg("default", "Red"),
        # Test #3: test no match of defined ALLOWED value
        "test_pattern_no_allowed_match.vspec": get_log_msg("allowed", "Red"),
        # Test #4: test no match of defined ALLOWED list of values
        "test_pattern_no_allowed_array_match.vspec": get_log_msg("allowed", "Red"),
    }

    def run_no_match_pattern_test(test_name: str, log_message: str):
        spec = HERE / test_name
        output = tmp_path / "out.json"
        log = tmp_path / "log.txt"
        cmd = f"vspec --log-file {log} export json --pretty -u {TEST_UNITS} -q {TEST_QUANT}"
        cmd += f" --vspec {spec} --output {output} --strict"
        process = subprocess.run(cmd.split())

        # Tested command should fail
        assert process.returncode != 0
        # Check logged error message
        assert log_message in log.read_text()

    # Run no_pattern_match_tests_to_run
    for tst_name, tst_msg in no_pattern_match_tests_to_run.items():
        run_no_match_pattern_test(tst_name, tst_msg)


def test_datatype_pattern_ok(tmp_path):
    # Test #1: test no match of defined DEFAULT value
    spec = HERE / "test_pattern_ok.vspec"
    output = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json --pretty -u {TEST_UNITS} -q {TEST_QUANT}"
    cmd += f" --vspec {spec} --output {output} --strict"
    process = subprocess.run(cmd.split())
    assert process.returncode == 0
