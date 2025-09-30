# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from vss_tools.tree import VSSNode


def test_fqn() -> None:
    foo_bar_baz = VSSNode(
        "baz",
        None,
        {"type": "sensor", "description": "foo.bar.baz", "datatype": "int8"},
    )

    foo_bar = VSSNode(
        "bar",
        None,
        {"type": "branch", "description": "foo.bar"},
        children=[foo_bar_baz],
    )

    _ = VSSNode("foo", None, {"type": "branch", "description": "foo"}, children=[foo_bar])

    assert foo_bar_baz.name == "baz"
    assert foo_bar_baz.get_fqn() == "foo.bar.baz"
    assert foo_bar_baz.data.fqn == "foo.bar.baz"
