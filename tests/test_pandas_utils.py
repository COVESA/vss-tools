"""
Tests for pandas utilities.
"""

from pathlib import Path

import pandas as pd

from vss_tools.main import get_trees
from vss_tools.utils.pandas_utils import get_metadata_df


class TestPandasUtils:
    """Test class for pandas utilities."""

    def test_get_metadata_df_basic_structure(self):
        """Test that get_metadata_df returns proper DataFrames with expected structure."""
        # Load a simple example vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        branches_df, leaves_df = get_metadata_df(tree)

        # Test that we get DataFrames back
        assert isinstance(branches_df, pd.DataFrame)
        assert isinstance(leaves_df, pd.DataFrame)

        # Test DataFrame structure (fqn is the index, not a column)
        expected_branch_headers = [
            "parent", "name", "type", "description", "comment", "deprecation", "instances"
        ]
        expected_leaf_headers = [
            "parent", 
            "name",
            "type",
            "description",
            "comment",
            "deprecation",
            "datatype",
            "unit",
            "min",
            "max",
            "allowed",
            "default",
        ]

        assert list(branches_df.columns) == expected_branch_headers
        assert list(leaves_df.columns) == expected_leaf_headers

        # Test that DataFrames have proper index
        assert branches_df.index.name == "fqn"
        assert leaves_df.index.name == "fqn"

        # Test that DataFrames are sorted by index
        assert branches_df.index.is_monotonic_increasing
        assert leaves_df.index.is_monotonic_increasing

    def test_get_metadata_df_content_validation(self):
        """Test that get_metadata_df extracts correct content from VSS tree."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        branches_df, leaves_df = get_metadata_df(tree)

        # Test that we have some data
        assert len(branches_df) > 0
        assert len(leaves_df) > 0

        # Test specific content - check for Vehicle branch
        assert "Vehicle" in branches_df.index
        vehicle_row = branches_df.loc["Vehicle"]
        assert vehicle_row["type"] == "branch"
        assert vehicle_row["name"] == "Vehicle"
        assert vehicle_row["parent"] is None  # Root node has None parent

        # Test that branches only contain branch type nodes
        assert all(branches_df["type"] == "branch")

        # Test that leaves only contain leaf type nodes (attribute, sensor, actuator)
        assert all(leaves_df["type"].isin(["attribute", "sensor", "actuator"]))

        # Test that leaf nodes have proper parent relationships
        for fqn, leaf_row in leaves_df.iterrows():
            parent_fqn = leaf_row["parent"]
            if parent_fqn:  # Not root level
                # Parent should either be in branches_df or be None for root
                assert parent_fqn in branches_df.index or parent_fqn is None

    def test_get_metadata_df_with_instances_and_constraints(self):
        """Test get_metadata_df handles instances and constraints properly."""
        # Load the example seat vspec which should have instances
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        branches_df, leaves_df = get_metadata_df(tree)

        # Look for nodes with instances (seat example should have some)
        branches_with_instances = branches_df[branches_df["instances"].notna()]
        
        # We should have at least some branches with instances based on the seat example
        if len(branches_with_instances) > 0:
            # Check that instances are properly captured
            for fqn, row in branches_with_instances.iterrows():
                instances = row["instances"]
                assert instances is not None
                # Instances should be a list or similar structure
                assert hasattr(instances, '__iter__')

        # Test specific allowed values we know exist
        if "Vehicle.Cabin.DriverPosition" in leaves_df.index:
            driver_pos = leaves_df.loc["Vehicle.Cabin.DriverPosition"]
            allowed = driver_pos["allowed"]
            assert isinstance(allowed, list)
            assert len(allowed) > 0
            # Should contain the expected values from the vspec
            assert "LEFT" in allowed

        # Test that we have branches with instances (Seat should have instances)
        if "Vehicle.Cabin.Seat" in branches_df.index:
            seat_row = branches_df.loc["Vehicle.Cabin.Seat"]
            instances = seat_row["instances"]
            assert instances is not None
            assert len(instances) > 0
