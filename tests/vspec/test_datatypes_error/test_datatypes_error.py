#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import os
import subprocess
from pathlib import Path


def test_datatype_error(tmp_path):
    cmd = (
        f"vspec2json --json-pretty -u ../test_units.yaml test.vspec ${tmp_path / 'out.json'}"
    )
    env = os.environ.copy()
    env["COLUMNS"] = "120"
    p = subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent,
        env=env,
    )
    assert p.returncode != 0

    assert (
        "Following types were referenced in signals but have not been defined"
        in p.stdout)


def test_datatype_branch(tmp_path):
    cmd = (
        "vspec2json --json-pretty -u ../test_units.yaml "
        f"test_datatype_branch.vspec ${tmp_path / 'out.json'}"
    )
    env = os.environ.copy()
    env["COLUMNS"] = "120"
    p = subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent,
        env=env,
    )
    assert p.returncode != 0

    assert (
        "cannot have datatype"
        in p.stdout
    )
