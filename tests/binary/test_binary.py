# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "vspec" / "test_units.yaml"
TEST_QUANT = HERE / ".." / "vspec" / "test_quantities.yaml"
BIN_DIR = HERE / ".." / ".." / "binary"


def check_expected_for_tool(tool_path, signal_name: str, grep_str: str, test_binary):
    stdin = f"m\n{signal_name}\n1\nq"
    cmd = f"{tool_path} {test_binary}"
    process = subprocess.run(cmd.split(), input=stdin, check=True, capture_output=True, text=True)
    print(process.stdout)
    assert grep_str in process.stdout


def test_binary(tmp_path):
    """
    Tests binary tools by generating binary file and using test parsers to interpret them and request
    some basic information.
    """

    test_binary = tmp_path / "test.binary"
    ctestparser = tmp_path / "ctestparser"
    gotestparser = tmp_path / "gotestparser"
    bintool_lib = tmp_path / "binarytool.so"
    cmd = f"gcc -shared -o {bintool_lib} -fPIC {BIN_DIR / 'binarytool.c'}"
    subprocess.run(cmd.split(), check=True)
    cmd = f"vspec export binary -b {bintool_lib} -u {TEST_UNITS}"
    cmd += f" -q {TEST_QUANT} -s {HERE / 'test.vspec'} -o {test_binary}"
    subprocess.run(cmd.split(), check=True)
    cmd = f"cc {BIN_DIR / 'c_parser/testparser.c'} {BIN_DIR / 'c_parser/cparserlib.c'} -o {ctestparser}"
    subprocess.run(cmd.split(), check=True)
    cmd = f"go build -o {gotestparser} testparser.go"
    subprocess.run(cmd.split(), check=True, cwd=BIN_DIR / "go_parser")

    parsers = [ctestparser, gotestparser]
    for parser in parsers:
        check_expected_for_tool(parser, "A.String", "Node type=SENSOR", test_binary)
        check_expected_for_tool(parser, "A.Int", "Node type=ACTUATOR", test_binary)
