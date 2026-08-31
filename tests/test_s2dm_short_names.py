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

    def test_cross_tree_collision_detection(self):
        """Test collision detection works across main tree and struct types."""
        tree, data_type_tree = get_trees(
            vspec=Path("tests/vspec/test_s2dm_cross_tree_collisions/test.vspec"),
            types=(Path("tests/vspec/test_s2dm_cross_tree_collisions/types.vspec"),),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        # Generate schema with short names enabled
        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(
            tree, data_type_tree, use_short_names=True
        )
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Verify collision detection ran and found collisions
        assert vspec_comments["short_name_mapping"] is not None
        assert len(vspec_comments["short_name_collisions"]) > 0

        # Window collisions: 3 branches with "Window" name
        # - Vehicle.Body.Window
        # - Vehicle.Cabin.Window
        # - VehicleDataTypes.Window (struct)
        # Should get parent-qualified names
        assert "type Body_Window @vspec" in schema_str
        assert "type Cabin_Window @vspec" in schema_str
        assert "type VehicleDataTypes_Window @vspec" in schema_str

        # Status collisions: 2 branches with "Status" name
        # - Vehicle.Powertrain.Status
        # - VehicleDataTypes.Status (struct)
        # Should get parent-qualified names
        assert "type Powertrain_Status @vspec" in schema_str
        assert "type VehicleDataTypes_Status @vspec" in schema_str

        # Sensor is unique (only in structs) - should use short name
        assert "type Sensor @vspec" in schema_str

        # Verify collision groups contain both main tree and struct types
        collision_groups = {c["short_name"]: c for c in vspec_comments["short_name_collisions"]}

        # Window collision group should have 3 FQNs
        assert "Window" in collision_groups
        window_group = collision_groups["Window"]
        assert window_group["collision_count"] == 3
        assert "Vehicle.Body.Window" in window_group["fqns"]
        assert "Vehicle.Cabin.Window" in window_group["fqns"]
        assert "VehicleDataTypes.Window" in window_group["fqns"]

        # Status collision group should have 2 FQNs
        assert "Status" in collision_groups
        status_group = collision_groups["Status"]
        assert status_group["collision_count"] == 2
        assert "Vehicle.Powertrain.Status" in status_group["fqns"]
        assert "VehicleDataTypes.Status" in status_group["fqns"]
