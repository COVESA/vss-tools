# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import pytest
import subprocess

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "vspec" / "test_units.yaml"
BIN_DIR = HERE / ".." / ".." / "binary"


def check_expected_for_tool(tool_path, signal_name: str, grep_str: str, test_binary):
    stdin = f"m\n{signal_name}\n1\nq"
    cmd = f"{tool_path} {test_binary}"
    process = subprocess.run(
        cmd.split(), input=stdin, check=True, capture_output=True, text=True
    )
    print(process.stdout)
    assert grep_str in process.stdout


@pytest.mark.parametrize("parser", ["ctestparser", "gotestparser"])
@pytest.mark.parametrize("test_id", [False, True])
def test_binary(tmp_path, parser: str, test_id: bool):
    """
    Tests binary tools by generating binary file and using test parsers to interpret them and request
    some basic information.
    """

    test_binary = tmp_path / "test.binary"
    testparser = tmp_path / parser

    cmd = (
        f"gcc -shared -o {tmp_path / 'binarytool.so'} -fPIC {BIN_DIR / 'binarytool.c'}"
    )
    subprocess.run(cmd.split(), check=True)

    if test_id:
        cmd = f"vspec2id -u {TEST_UNITS} {HERE / 'test.vspec'} {tmp_path / 'test_id.vspec'}"
        subprocess.run(cmd.split(), check=True)
        cmd = f"vspec2binary -u {TEST_UNITS} {tmp_path / 'test_id.vspec'} {test_binary}"
        subprocess.run(cmd.split(), check=True)
    else:
        cmd = f"vspec2binary -u {TEST_UNITS} {HERE / 'test.vspec'} {test_binary}"
        subprocess.run(cmd.split(), check=True)

    if parser == "ctestparser":
        cmd = f"cc {BIN_DIR / 'c_parser/testparser.c'} {BIN_DIR / 'c_parser/cparserlib.c'} -o {testparser}"
        subprocess.run(cmd.split(), check=True)
    elif parser == "gotestparser":
        cmd = f"go build -o {testparser} testparser.go"
        subprocess.run(cmd.split(), check=True, cwd=BIN_DIR / "go_parser")

    check_expected_for_tool(testparser, "A.String", "Node type=SENSOR", test_binary)
    check_expected_for_tool(testparser, "A.Int", "Node type=ACTUATOR", test_binary)
