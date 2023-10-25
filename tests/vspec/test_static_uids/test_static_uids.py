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
    "layer, id_counter, gen_no_layer, decimal_output, result_static_UID",
    [
        (99, 1, False, False, "00000263"),
        (0, 4, True, False, "000005"),
        (0, 5, False, True, "000006"),
    ],
)
def test_generate_id(
    layer, id_counter, gen_no_layer, decimal_output, result_static_UID
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
        offset=1,
        layer=layer,
        no_layer=gen_no_layer,
        decimal_output=decimal_output,
    )

    assert result == result_static_UID


@pytest.mark.parametrize(
    "layer, id_counter, gen_no_layer, decimal_output, result_static_UID",
    [
        (99, 1, False, False, "0x00000263"),
        (0, 4, True, False, "0x000005"),
        (0, 5, False, True, "000006"),
    ],
)
def test_export_node(
    request, layer, id_counter, gen_no_layer, decimal_output, result_static_UID
):
    dir_path = os.path.dirname(request.fspath)
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
        offset=1,
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
            "Currently we don't support decimal ouputs with layer!"
        )

    assert result_dict == yaml_dict


# INTEGRATION TESTS


def test_full_script(change_test_dir, caplog):
    validation_file = "./validation_vspecs/validation.vspec"
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
    validation_file = "./validation_vspecs/validation_uid.vspec"
    cla_str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 3 and all(
        log.levelname == "WARNING" for log in caplog.records
    )


def test_changed_unit(change_test_dir, caplog):
    validation_file = "./validation_vspecs/validation_unit.vspec"
    cla_str = (
        "../../../vspecID.py ./test.vspec ./out.vspec "
        "--gen-layer-ID-offset 99 --validate-static-uid "
        + validation_file
        + " --validate-automatic-mode --only-validate-no-export"
    )
    clas = shlex.split(cla_str)
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 4 and all(
        log.levelname == "WARNING" for log in caplog.records
    )


def test_changed_datatype(change_test_dir, caplog):
    validation_file = "./validation_vspecs/validation_datatype.vspec"
    cla_str = (
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
