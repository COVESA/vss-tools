# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Tests for S2DM short name collision detection and resolution.

These tests are based on real-world collision scenarios documented in:
https://github.com/COVESA/vehicle_signal_specification/issues/790
"""

from pathlib import Path

from vss_tools.exporters.s2dm import generate_s2dm_schema, print_schema_with_vspec_directives
from vss_tools.main import get_trees


class TestS2DMShortNames:
    """Test short name collision detection and resolution in S2DM exporter."""

    def test_basic_short_name_no_collision(self):
        """Test that unique branch names use short names without collision."""
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        # Generate schema with short names enabled (default)
        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree, use_short_names=True)
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Should use short names for unique branches
        assert "type Vehicle @vspec" in schema_str
        assert "type Cabin @vspec" in schema_str
        assert "type Seat @vspec" in schema_str

        # Should NOT use FQN-style names
        assert "type Vehicle_Cabin @vspec" not in schema_str
        assert "type Vehicle_Cabin_Seat @vspec" not in schema_str

    def test_fqn_type_names_flag(self):
        """Test that use_short_names=False uses full FQN instead of short names."""
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        # Generate schema with short names disabled (use_short_names=False)
        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree, use_short_names=False)
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Should use FQN-style names
        assert "type Vehicle @vspec" in schema_str
        assert "type Vehicle_Cabin @vspec" in schema_str
        assert "type Vehicle_Cabin_Seat @vspec" in schema_str

        # Short name collision detection should be skipped
        assert vspec_comments["short_name_mapping"] is None
        assert vspec_comments["short_name_collisions"] == []
