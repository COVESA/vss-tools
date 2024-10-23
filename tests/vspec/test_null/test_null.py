# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def run_exporter(exporter, tmp_path):
    vspec = HERE / "test.vspec"
    output = tmp_path / f"out.{exporter}"
    expected = HERE / f"expected.{exporter}"
    if not expected.exists():
        return
    cmd = f"vspec export {exporter} --vspec {vspec} --output {output} -e foo -e bar"
    subprocess.run(cmd.split(), check=True)
    with open(output) as f:
        out_content = yaml.safe_load(f)
    assert "foo" in out_content["Vehicle"]
    assert "bar" in out_content["Vehicle"]
    assert out_content["Vehicle"]["foo"] is None
    assert out_content["Vehicle"]["bar"] is None


def test_null(tmp_path):
    exporters = ["yaml"]

    for exporter in exporters:
        run_exporter(exporter, tmp_path)
