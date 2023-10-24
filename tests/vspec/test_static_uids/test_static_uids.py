#!/usr/bin/env python3

import pytest
import os
import shlex
import logging
import argparse
import vspec2x


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


def test_full_script(change_test_dir, caplog):
    validation_file = "./validation.vspec"
    cla_str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)

    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 0


def test_changed_uid(change_test_dir, caplog):
    validation_file = "./validation_uid.vspec"
    cla_str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)

    print(f"{clas=}")

    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 3 and all(
        log.levelname == "WARNING" for log in caplog.records
    )


def test_changed_unit(change_test_dir, caplog):
    validation_file = "./validation_unit.vspec"
    cla_str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)

    print(f"{clas=}")

    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 4 and all(
        log.levelname == "WARNING" for log in caplog.records
    )


def test_changed_datatype(change_test_dir, caplog):
    validation_file = "./validation_datatype.vspec"
    cla_str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)

    print(f"{clas=}")

    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
