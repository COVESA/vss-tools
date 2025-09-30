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


def test_struct_default(tmp_path):
    vspec = HERE / "struct_default_model_ok.vspec"
    types = HERE / "struct_default_types.vspec"
    cmd = f"vspec export tree -s {vspec} -t {types}"

    # ok
    p = subprocess.run(cmd.split())
    assert p.returncode == 0

    # nok
    log = tmp_path / "log.txt"
    vspec = HERE / "struct_default_model_nok.vspec"
    cmd = f"vspec --log-file {log} export tree -s {vspec} -t {types}"
    p = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert p.returncode != 0
    print(log.read_text())
    assert "invalid 'default' format for datatype 'Types.T'" in log.read_text()
