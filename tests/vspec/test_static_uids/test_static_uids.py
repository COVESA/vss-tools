#!/usr/bin/env python3

import os
import pytest
import shlex
import vspec
import vspec.vssexporters.vss2id as vss2id
import vspec2x
import yaml

from typing import Dict, Optional
from vspec.model.constants import VSSTreeType, VSSDataType, VSSConstant
from vspec.model.vsstree import VSSNode
from vspec.utils.idgen_utils import get_all_keys_values


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


def get_test_node(
    node_name: str, unit: str, datatype: VSSDataType, allowed: str
) -> VSSNode:
    source = {
        "description": "some desc",
        "type": "branch",
        "$file_name$": "testfile",
    }
    node = VSSNode(node_name, source, VSSTreeType.SIGNAL_TREE.available_types())
    node.unit = VSSConstant(label=str(unit), value=str(unit))
    node.data_type_str = datatype.value
    node.validate_and_set_datatype()
    node.allowed = allowed
    # node.min = minimum
    # node.max = maximum
    #
    return node


# FIXTURES


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


# UNIT TESTS


@pytest.mark.parametrize(
    "node_name, unit, datatype, allowed, minimum, maximum, layer_id_offset, result_static_uid",
    [
        ("TestNode", "m", VSSDataType.INT8, "", 0, 10000, 0, "1692F5DF"),
        ("TestNode", "mm", VSSDataType.UINT32, "", "", "", 99, "31A8FA63"),
        ("TestNodeChild", "degrees/s", VSSDataType.FLOAT, "", "", "", 0, "E61220E6"),
        (
            "TestNodeChild",
            "percent",
            VSSDataType.STRING,
            ["YES", "NO"],
            0,
            100,
            112,
            "659CF970",
        ),
    ],
)
def test_generate_id(
    node_name: str,
    unit: str,
    datatype: VSSDataType,
    allowed: str,
    minimum: Optional[int],
    maximum: Optional[int],
    layer_id_offset: int,
    result_static_uid: str,
):
    node = get_test_node(node_name, unit, datatype, allowed)
    result, _ = vss2id.generate_split_id(
        node, id_counter=0, gen_layer_id_offset=layer_id_offset
    )

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


@pytest.mark.parametrize(
    "children_names",
    [
        ["ChildNode", "ChildNode"],
        ["ChildNode", "ChildNodeDifferentName"],
    ],
)
def test_duplicate_hash(caplog: pytest.LogCaptureFixture, children_names: list):
    tree = get_test_node("TestNode", "m", VSSDataType.UINT32, "")
    child_node = get_test_node(children_names[0], "m", VSSDataType.UINT32, "")
    child_node2 = get_test_node(children_names[1], "m", VSSDataType.UINT32, "")
    tree.children = [child_node, child_node2]

    yaml_dict: Dict[str, dict] = {}
    if children_names[0] == children_names[1]:
        # assert system exit and log
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            vss2id.export_node(
                yaml_dict,
                tree,
                id_counter=0,
                gen_layer_id_offset=0,
            )
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == -1
        assert len(caplog.records) == 1 and all(
            log.levelname == "CRITICAL" for log in caplog.records
        )
    else:
        # assert all IDs different
        vss2id.export_node(
            yaml_dict,
            tree,
            id_counter=0,
            gen_layer_id_offset=0,
        )
        assigned_ids: list = []
        for key, value in get_all_keys_values(yaml_dict):
            if not isinstance(value, dict) and key == "staticUID":
                assigned_ids.append(value)
        assert len(assigned_ids) == len(set(assigned_ids))


# INTEGRATION TESTS


@pytest.mark.usefixtures("change_test_dir")
def test_full_script(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 0


@pytest.mark.usefixtures("change_test_dir")
def test_semantic(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation_semantic_change.vspec"
    clas = shlex.split(get_cla_validation(validation_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "SEMANTIC NAME CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_vss_path(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_vss_path.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "PATH CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_unit(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_unit.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_datatype(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_datatype.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_name_datatype(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_name_datatype.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_deprecation(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_deprecation.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "DEPRECATION MSG CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_description(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_description.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "DESCRIPTION MISMATCH" in record.msg
