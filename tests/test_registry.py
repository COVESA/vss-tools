# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest
import yaml
from vss_tools.utils.registry_utils import (
    REGISTRY_COLUMNS,
    NamespacesConfig,
    RegistryConfigException,
    RegistryIntegrityException,
    _hash_row,
    empty_registry,
    load_namespaces,
    load_registry,
    sync_registry,
    to_jsonld,
    validate_immutability,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VSPEC = Path("tests/vspec/test_s2dm/example_seat.vspec")
QUANTITIES = Path("tests/vspec/test_s2dm/test_quantities.yaml")
UNITS = Path("tests/vspec/test_s2dm/test_units.yaml")

SAMPLE_FQNS = [
    "Vehicle",
    "Vehicle.Cabin",
    "Vehicle.Cabin.DriverPosition",
    "Vehicle.Cabin.Seat",
    "Vehicle.VehicleIdentification",
    "Vehicle.VehicleIdentification.VIN",
]


@pytest.fixture
def sample_fqns() -> list[str]:
    """A representative sorted list of FQNs (subset matching example_seat.vspec branches)."""
    return sorted(SAMPLE_FQNS)


@pytest.fixture
def sample_namespaces() -> dict:
    return {
        "namespace": {
            "prefix": "eg",
            "uri": "https://www.example.org/myModel#",
            "description": "Example overlay model",
        },
        "imports": {
            "covss": {"uri": "https://www.covesa.global/model/vss#", "description": "COVESA VSS"},
        },
    }


# ---------------------------------------------------------------------------
# Unit tests — pure functions
# ---------------------------------------------------------------------------


class TestHashRow:
    def test_deterministic(self):
        assert _hash_row("covss:0", "Vehicle") == _hash_row("covss:0", "Vehicle")

    def test_different_inputs_differ(self):
        assert _hash_row("covss:0", "Vehicle") != _hash_row("covss:0", "Vehicle.Cabin")

    def test_hex_64_chars(self):
        h = _hash_row("covss:0", "Vehicle")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestEmptyRegistry:
    def test_columns(self):
        df = empty_registry()
        assert list(df.columns) == REGISTRY_COLUMNS

    def test_empty(self):
        assert len(empty_registry()) == 0


class TestLoadNamespaces:
    def test_valid(self, tmp_path: Path, sample_namespaces: dict):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(yaml.dump(sample_namespaces))
        config = load_namespaces(ns_file)
        assert isinstance(config, NamespacesConfig)
        assert config.namespace.prefix == "eg"
        assert config.namespace.uri == "https://www.example.org/myModel#"
        assert "covss" in config.imports
        assert config.imports["covss"].uri == "https://www.covesa.global/model/vss#"

    def test_no_imports_is_valid(self, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(yaml.dump({"namespace": {"prefix": "eg", "uri": "https://example.org/"}}))
        config = load_namespaces(ns_file)
        assert config.imports == {}

    def test_missing_namespace_key_raises(self, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(yaml.dump({"imports": {"covss": {"uri": "https://covesa.global/"}}}))
        with pytest.raises(RegistryConfigException):
            load_namespaces(ns_file)

    def test_missing_uri_raises(self, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(yaml.dump({"namespace": {"prefix": "eg", "description": "no uri"}}))
        with pytest.raises(RegistryConfigException):
            load_namespaces(ns_file)

    def test_missing_prefix_raises(self, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(yaml.dump({"namespace": {"uri": "https://example.org/"}}))
        with pytest.raises(RegistryConfigException):
            load_namespaces(ns_file)

    def test_owned_prefix_in_imports_raises(self, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(
            yaml.dump(
                {
                    "namespace": {"prefix": "eg", "uri": "https://example.org/"},
                    "imports": {"eg": {"uri": "https://example.org/"}},
                }
            )
        )
        with pytest.raises(RegistryConfigException):
            load_namespaces(ns_file)

    def test_not_a_mapping_raises(self, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text("- item1\n- item2\n")
        with pytest.raises(RegistryConfigException):
            load_namespaces(ns_file)

    def test_invalid_yaml_raises(self, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text("key: [unclosed")
        with pytest.raises(RegistryConfigException):
            load_namespaces(ns_file)


class TestSyncRegistry:
    def test_first_run_mints_all(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, minted = sync_registry(df, sample_fqns, "covss")
        assert minted == len(sample_fqns)
        assert len(updated) == len(sample_fqns)

    def test_ids_start_at_zero(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        assert updated["int_id"].min() == 0

    def test_ids_are_contiguous(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        ids = sorted(updated[updated["composed_id"].str.startswith("covss:")]["int_id"].tolist())
        assert ids == list(range(len(sample_fqns)))

    def test_idempotent(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        updated2, minted2 = sync_registry(updated, sample_fqns, "covss")
        assert minted2 == 0
        assert len(updated2) == len(sample_fqns)

    def test_new_fqn_mints_one(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        new_fqns = sample_fqns + ["Vehicle.NewBranch"]
        updated2, minted2 = sync_registry(updated, sorted(new_fqns), "covss")
        assert minted2 == 1
        assert len(updated2) == len(sample_fqns) + 1

    def test_composed_id_format(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        for cid in updated["composed_id"]:
            prefix, int_part = cid.split(":", 1)
            assert prefix == "covss"
            assert int_part.isdigit()

    def test_prefix_isolation(self, sample_fqns: list[str]):
        """Each namespace prefix starts from 0 independently."""
        df = empty_registry()
        df, _ = sync_registry(df, sample_fqns, "covss")

        eg_fqns = ["Other.Branch", "Other.Branch.Leaf"]
        df, minted = sync_registry(df, eg_fqns, "eg")
        assert minted == 2

        eg_rows = df[df["composed_id"].str.startswith("eg:")]
        assert sorted(eg_rows["int_id"].tolist()) == [0, 1]
        assert eg_rows["composed_id"].tolist() == ["eg:0", "eg:1"]

    def test_row_hashes_are_correct(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        for _, row in updated.iterrows():
            assert row["row_hash"] == _hash_row(row["composed_id"], row["fqn"])


class TestValidateImmutability:
    def test_passes_on_equal(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        validate_immutability(updated, updated.copy())  # should not raise

    def test_passes_on_empty_old(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        validate_immutability(empty_registry(), updated)  # should not raise

    def test_raises_on_fqn_change(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        corrupted = updated.copy()
        corrupted.loc[0, "fqn"] = "Tampered.FQN"
        with pytest.raises(RegistryIntegrityException):
            validate_immutability(updated, corrupted)

    def test_raises_on_int_id_change(self, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        corrupted = updated.copy()
        corrupted.loc[0, "int_id"] = 9999
        with pytest.raises(RegistryIntegrityException):
            validate_immutability(updated, corrupted)


class TestLoadRegistry:
    def test_roundtrip(self, tmp_path: Path, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        csv_path = tmp_path / "registry.csv"
        updated.to_csv(csv_path, index=False)

        loaded = load_registry(csv_path)
        assert len(loaded) == len(sample_fqns)
        assert list(loaded.columns) == REGISTRY_COLUMNS

    def test_hash_mismatch_raises(self, tmp_path: Path, sample_fqns: list[str]):
        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "covss")
        csv_path = tmp_path / "registry.csv"
        updated.to_csv(csv_path, index=False)

        # Corrupt a row's fqn after writing
        lines = csv_path.read_text().splitlines()
        lines[1] = lines[1].replace(sample_fqns[0], "Tampered.FQN")
        csv_path.write_text("\n".join(lines) + "\n")

        with pytest.raises(RegistryIntegrityException):
            load_registry(csv_path)


class TestToJsonLD:
    def test_shape(self, sample_fqns: list[str], sample_namespaces: dict, tmp_path: Path):
        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(yaml.dump(sample_namespaces))
        config = load_namespaces(ns_file)

        df = empty_registry()
        updated, _ = sync_registry(df, sample_fqns, "eg")

        doc = to_jsonld(updated, config)
        assert "@context" in doc
        assert "@graph" in doc

        # Owned namespace appears in context
        assert "eg" in doc["@context"]
        assert doc["@context"]["eg"] == "https://www.example.org/myModel#"

        # Imported namespaces also appear in context
        assert "covss" in doc["@context"]
        assert doc["@context"]["covss"] == "https://www.covesa.global/model/vss#"

        graph = doc["@graph"]
        assert len(graph) == len(sample_fqns)
        for entry in graph:
            assert "@id" in entry
            assert "fqn" in entry
            assert "status" in entry


# ---------------------------------------------------------------------------
# Integration test — sync end-to-end with real vspec
# ---------------------------------------------------------------------------


class TestSyncEndToEnd:
    def test_sync_real_vspec(self, tmp_path: Path):
        """Full end-to-end: load real vspec, sync registry, reload and validate."""
        from anytree import PreOrderIter
        from vss_tools.main import get_trees

        tree, _ = get_trees(
            vspec=VSPEC,
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(QUANTITIES,),
            units=(UNITS,),
            overlays=(),
            expand=False,
        )
        fqns = sorted(node.get_fqn() for node in PreOrderIter(tree))

        ns_file = tmp_path / "namespaces.yaml"
        ns_file.write_text(
            yaml.dump(
                {
                    "namespace": {"prefix": "covss", "uri": "https://www.covesa.global/model/vss#"},
                }
            )
        )
        registry_path = tmp_path / "registry.csv"

        df, minted = sync_registry(empty_registry(), fqns, "covss")
        assert minted == len(fqns)
        df.to_csv(registry_path, index=False)

        # Reload and verify integrity
        loaded = load_registry(registry_path)
        assert len(loaded) == len(fqns)

        # Second sync is idempotent
        df2, minted2 = sync_registry(loaded, fqns, "covss")
        assert minted2 == 0
        assert len(df2) == len(fqns)
