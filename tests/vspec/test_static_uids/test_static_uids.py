#!/usr/bin/env python3

import os
import pytest
import shlex
import vspec
import vspec.vssexporters.vssidgen as vssidgen
import vspec2x
import yaml

from typing import Dict
from vspec.model.constants import VSSTreeType
from vspec.model.vsstree import VSSNode


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


# UNIT TESTS


@pytest.mark.parametrize(
    "layer, id_counter, offset, gen_no_layer, decimal_output, result_static_uid",
    [
        (99, 1, 1, False, False, "00000263"),
        (0, 4, 3, True, False, "000007"),
        (0, 5, 1, False, True, "000006"),
    ],
)
def test_generate_id(
    layer: int,
    id_counter: int,
    offset: int,
    gen_no_layer: bool,
    decimal_output: bool,
    result_static_uid: str,
):
    source = {
        "description": "some desc",
        "type": "branch",
        "uuid": "26d6e362-a422-11ea-bb37-0242ac130002",
        "$file_name$": "testfile",
    }
    node = VSSNode("TestNode", source, VSSTreeType.SIGNAL_TREE.available_types())

    result, _ = vssidgen.generate_split_id(
        node,
        id_counter,
        offset=offset,
        layer=layer,
        no_layer=gen_no_layer,
        decimal_output=decimal_output,
    )

    assert result == result_static_uid


@pytest.mark.parametrize(
    "layer, id_counter, offset, gen_no_layer, decimal_output",
    [
        (99, 1, 1, False, False),
        (0, 4, 100, True, False),
        (0, 5, 1, False, True),
    ],
)
def test_export_node(
    request: pytest.FixtureRequest,
    layer: int,
    id_counter: int,
    offset: int,
    gen_no_layer: bool,
    decimal_output: bool,
):
    dir_path = os.path.dirname(request.path)
    vspec_file = os.path.join(dir_path, "test.vspec")

    vspec.load_units(vspec_file, [os.path.join(dir_path, "units.yaml")])
    tree = vspec.load_tree(
        vspec_file, include_paths=["."], tree_type=VSSTreeType.SIGNAL_TREE
    )

    yaml_dict: Dict[str, str] = {}
    vssidgen.export_node(
        yaml_dict,
        tree,
        id_counter,
        offset=offset,
        layer=layer,
        no_layer=gen_no_layer,
        decimal_output=decimal_output,
    )

    result_dict: Dict[str, str]
    if decimal_output:
        with open(
            os.path.join(dir_path, "validation_yamls/validation_decimal.yaml"), "r"
        ) as f:
            result_dict = yaml.load(f, Loader=yaml.FullLoader)
    elif gen_no_layer and not decimal_output:
        with open(
            os.path.join(dir_path, "validation_yamls/validation_hex_no_layer.yaml"), "r"
        ) as f:
            result_dict = yaml.load(f, Loader=yaml.FullLoader)
    elif not gen_no_layer and not decimal_output:
        with open(
            os.path.join(dir_path, "validation_yamls/validation_hex_layer.yaml"), "r"
        ) as f:
            result_dict = yaml.load(f, Loader=yaml.FullLoader)
    else:
        raise NotImplementedError(
            "Currently we don't support decimal outputs with layer!"
        )

    assert result_dict == yaml_dict


# INTEGRATION TESTS


@pytest.mark.usefixtures("change_test_dir")
def test_full_script(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation.vspec"
    cla_str: str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 0


@pytest.mark.usefixtures("change_test_dir")
def test_changed_description(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation_description.vspec"
    cla_str: str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "DESCRIPTION MISMATCH" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_changed_uid(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation_uid.vspec"
    cla_str: str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "UID MISMATCH" or "UID CHANCE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_changed_unit(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation_unit.vspec"
    cla_str: str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "UNIT MISMATCH" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_changed_datatype(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation_datatype.vspec"
    cla_str: str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "DATATYPE MISMATCH" in record.msg