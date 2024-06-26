# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
import sys
from pathlib import Path
import os


def test_generator():
    cmd = [
        sys.executable,
        "example_generator.py",
        "-k",
        "VSS Contributor",
        "-u",
        "../vspec/test_units.yaml",
        "test.vspec",
    ]
    env = os.environ.copy()
    env["COLUMNS"] = "120"
    p = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=Path(__file__).resolve().parent, env=env)
    assert "I found 2 comments with vss contributor" in p.stdout
