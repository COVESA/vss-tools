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


def test_get_default_first_allowed_violations_clean() -> None:
    """Canonical pattern `allowed: ['UNKNOWN', ...]` + `default: 'UNKNOWN'` passes."""
    leaf = VSSNode(
        "Mode",
        None,
        {
            "type": "sensor",
            "description": "cabin mode",
            "datatype": "string",
            "allowed": ["UNKNOWN", "ECO", "SPORT"],
            "default": "UNKNOWN",
        },
    )
    root = VSSNode("Cabin", None, {"type": "branch", "description": "cabin"}, children=[leaf])
    assert root.get_default_first_allowed_violations() == []


def test_get_default_first_allowed_violations_mismatch() -> None:
    """Non-first-allowed default flagged with repro message."""
    leaf = VSSNode(
        "Mode",
        None,
        {
            "type": "sensor",
            "description": "cabin mode",
            "datatype": "string",
            "allowed": ["UNKNOWN", "ECO", "SPORT"],
            "default": "ECO",
        },
    )
    root = VSSNode("Cabin", None, {"type": "branch", "description": "cabin"}, children=[leaf])
    violations = root.get_default_first_allowed_violations()
    assert len(violations) == 1
    assert violations[0][0] == "Cabin.Mode"
    assert "default='ECO'" in violations[0][1]
    assert "allowed[0]='UNKNOWN'" in violations[0][1]


def test_get_default_first_allowed_violations_no_allowed() -> None:
    """Node without `allowed` is not a candidate — no violation."""
    leaf = VSSNode(
        "Speed",
        None,
        {"type": "sensor", "description": "vehicle speed", "datatype": "float", "default": 0.0},
    )
    root = VSSNode("Vehicle", None, {"type": "branch", "description": "vehicle"}, children=[leaf])
    assert root.get_default_first_allowed_violations() == []


def test_get_default_first_allowed_violations_no_default() -> None:
    """Node with `allowed` but no `default` is not a violation — user opted out of default."""
    leaf = VSSNode(
        "Mode",
        None,
        {
            "type": "sensor",
            "description": "cabin mode",
            "datatype": "string",
            "allowed": ["ECO", "SPORT"],
        },
    )
    root = VSSNode("Cabin", None, {"type": "branch", "description": "cabin"}, children=[leaf])
    assert root.get_default_first_allowed_violations() == []
