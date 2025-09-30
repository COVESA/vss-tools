# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from vss_tools.main import get_trees

HERE = Path(__file__).resolve().parent


def test_exporters():
    tree, _ = get_trees(
        vspec=HERE / "test.vspec",
    )
    door = tree.children[0]
    row1 = door.children[0]
    assert row1.data.is_instance
    door.children[1]
    assert row1.data.is_instance
    special = row1.children[0]
    assert not special.data.is_instance
