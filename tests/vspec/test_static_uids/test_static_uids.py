#!/usr/bin/env python3

import os
import pytest
import shlex
import vspec
import vspec.vssexporters.vss2id as vss2id
import vspec2x
import yaml

from typing import Dict
from vspec.model.constants import VSSTreeType, VSSDataType
from vspec.model.vsstree import VSSNode


# HELPERS


def get_cla_test(test_file: str):
    return (
        "../../../vspec2id.py "
        + test_file
        + " ./out.vspec --validate-static-uid "
        + "./validation_vspecs/validation.vspec "
        + "--only-validate-no-export"
    )


def get_cla_validation(validation_file: str):
    return (
        "../../../vspec2id.py ./test_vspecs/test.vspec ./out.vspec "
        "--validate-static-uid " + validation_file
    )


# FIXTURES


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


# UNIT TESTS


@pytest.mark.parametrize(
    "node_name, datatype, layer_id_offset, result_static_uid",
    [
        ("TestNode", VSSDataType.INT8, 0, "8C31FDC6"),
        ("TestNode", VSSDataType.UINT32, 99, "F8291C63"),
        ("TestNodeChild", VSSDataType.FLOAT, 0, "B4EDDADD"),
        ("TestNodeChild", VSSDataType.STRING, 112, "B32E3C70"),
    ],
)
def test_generate_id(
    node_name: str, datatype: VSSDataType, layer_id_offset: int, result_static_uid: str
):
    # ToDo test all breaking changes
    source = {
        "description": "some desc",
        "type": "branch",
        "uuid": "26d6e362-a422-11ea-bb37-0242ac130002",
        "$file_name$": "testfile",
    }
    id_counter = 0
    node = VSSNode(node_name, source, VSSTreeType.SIGNAL_TREE.available_types())
    node.data_type_str = datatype.value
    node.validate_and_set_datatype()

    result, _ = vss2id.generate_split_id(node, id_counter, layer_id_offset)

    assert result == result_static_uid


@pytest.mark.parametrize(
    "gen_layer_id_offset",
    [
        0,
        99,
    ],
)
def test_export_node(
    request: pytest.FixtureRequest,
    gen_layer_id_offset,
):
    dir_path = os.path.dirname(request.path)
    vspec_file = os.path.join(dir_path, "test_vspecs/test.vspec")

    vspec.load_units(vspec_file, [os.path.join(dir_path, "test_vspecs/units.yaml")])
    tree = vspec.load_tree(
        vspec_file, include_paths=["."], tree_type=VSSTreeType.SIGNAL_TREE
    )

    yaml_dict: Dict[str, str] = {}
    vss2id.export_node(
        yaml_dict,
        tree,
        id_counter=0,
        gen_layer_id_offset=gen_layer_id_offset,
    )

    result_dict: Dict[str, str]
    if gen_layer_id_offset:
        with open(
            os.path.join(dir_path, "validation_yamls/validation_layer.yaml"), "r"
        ) as f:
            result_dict = yaml.load(f, Loader=yaml.FullLoader)
    else:
        with open(
            os.path.join(dir_path, "validation_yamls/validation_no_layer.yaml"), "r"
        ) as f:
            result_dict = yaml.load(f, Loader=yaml.FullLoader)

    assert result_dict.keys() == yaml_dict.keys()
    assert result_dict == yaml_dict


# INTEGRATION TESTS


@pytest.mark.usefixtures("change_test_dir")
def test_full_script(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1


@pytest.mark.usefixtures("change_test_dir")
def test_semantic(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation_semantic_change.vspec"
    clas = shlex.split(get_cla_validation(validation_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for i, record in enumerate(caplog.records):
        if i == 0:
            continue
        else:
            assert "SEMANTIC NAME CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_vss_path(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_vss_path.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 3 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for i, record in enumerate(caplog.records):
        if i < 2:
            continue
        else:
            assert "PATH CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_unit(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_unit.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 3 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for i, record in enumerate(caplog.records):
        if i == 0:
            continue
        else:
            assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_datatype(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_datatype.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for i, record in enumerate(caplog.records):
        if i == 0:
            continue
        else:
            assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_name_datatype(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_name_datatype.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for i, record in enumerate(caplog.records):
        if i == 0:
            continue
        else:
            assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_description(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_description.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for i, record in enumerate(caplog.records):
        if i == 0:
            continue
        else:
            assert "DESCRIPTION MISMATCH" in record.msg
