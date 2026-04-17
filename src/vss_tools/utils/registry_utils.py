# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Utilities for the VSS spec identifier registry."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from pydantic import BaseModel, field_validator

REGISTRY_COLUMNS = ["composed_id", "fqn", "int_id", "status", "row_hash"]
COMPOSED_ID_RE = re.compile(r"^[a-z][a-z0-9]*:\d+$")


class RegistryIntegrityException(Exception):
    """Indicates a hash mismatch or an attempt to mutate an immutable registry field."""


class RegistryConfigException(Exception):
    """Indicates an invalid namespaces configuration file."""


class NamespaceEntry(BaseModel):
    uri: str
    description: str | None = None


class OwnedNamespace(NamespaceEntry):
    """The single namespace this project owns and mints IDs under."""

    prefix: str


class NamespacesConfig(BaseModel):
    """Parsed content of a namespaces.yaml file."""

    namespace: OwnedNamespace
    imports: dict[str, NamespaceEntry] = {}


class RegistryRow(BaseModel):
    composed_id: str
    fqn: str
    int_id: int
    status: Literal["active", "deprecated"]
    row_hash: str

    @field_validator("composed_id")
    @classmethod
    def valid_composed_id(cls, v: str) -> str:
        if not COMPOSED_ID_RE.match(v):
            raise ValueError(f"Invalid composed_id format: '{v}' (expected e.g. 'covss:0')")
        return v


def _hash_row(composed_id: str, fqn: str) -> str:
    """Returns SHA256 hex digest of the immutable fields of a registry row."""
    return hashlib.sha256(f"{composed_id}|{fqn}".encode()).hexdigest()


def load_namespaces(path: Path) -> NamespacesConfig:
    """
    Loads and validates a namespaces YAML file.

    Expected format::

        namespace:
          prefix: eg
          uri: "https://www.example.org/myModel#"
          description: "Optional description"

        imports:
          covss:
            uri: "https://www.covesa.global/model/vss#"
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise RegistryConfigException(f"Failed to parse {path}: {e}") from e

    if not isinstance(raw, dict):
        raise RegistryConfigException(f"{path} must be a YAML mapping")

    if "namespace" not in raw:
        raise RegistryConfigException(f"{path} must have a 'namespace' key")

    try:
        owned = OwnedNamespace(**raw["namespace"])
    except Exception as e:
        raise RegistryConfigException(f"Invalid 'namespace' entry in {path}: {e}") from e

    imports: dict[str, NamespaceEntry] = {}
    for prefix, entry in (raw.get("imports") or {}).items():
        if not isinstance(entry, dict):
            raise RegistryConfigException(f"Import entry for '{prefix}' must be a mapping")
        try:
            imports[prefix] = NamespaceEntry(**entry)
        except Exception as e:
            raise RegistryConfigException(f"Invalid import entry for '{prefix}': {e}") from e

    if owned.prefix in imports:
        raise RegistryConfigException(
            f"Owned prefix '{owned.prefix}' also appears in 'imports' — a project cannot import its own namespace"
        )

    return NamespacesConfig(namespace=owned, imports=imports)


def empty_registry() -> pd.DataFrame:
    """Returns an empty registry DataFrame with the correct column schema."""
    return pd.DataFrame(columns=REGISTRY_COLUMNS)


def load_registry(path: Path) -> pd.DataFrame:
    """
    Loads a registry CSV and validates schema and row hashes.
    Raises RegistryIntegrityException on any hash mismatch or schema error.
    """
    df = pd.read_csv(path, dtype={"composed_id": str, "fqn": str, "int_id": int, "status": str, "row_hash": str})

    for _, row in df.iterrows():
        try:
            RegistryRow(**row.to_dict())
        except Exception as e:
            raise RegistryIntegrityException(f"Schema validation failed for row {row.to_dict()}: {e}") from e

        expected = _hash_row(str(row["composed_id"]), str(row["fqn"]))
        if row["row_hash"] != expected:
            raise RegistryIntegrityException(
                f"Hash mismatch for '{row['composed_id']}' — registry may have been manually edited"
            )

    return df


def sync_registry(df: pd.DataFrame, fqns: list[str], prefix: str) -> tuple[pd.DataFrame, int]:
    """
    Mints new IDs for FQNs not already present in the registry under any prefix.
    IDs for the given prefix start at 0 and increment per entry in that namespace.
    Returns (updated_df, number_of_newly_minted_ids).
    """
    existing_fqns: set[str] = set(df["fqn"]) if not df.empty else set()
    new_fqns = [f for f in fqns if f not in existing_fqns]

    if not new_fqns:
        return df, 0

    prefix_mask = df["composed_id"].str.startswith(f"{prefix}:") if not df.empty else pd.Series([], dtype=bool)
    next_int_id = int(prefix_mask.sum())

    new_rows: list[dict] = []
    for i, fqn in enumerate(new_fqns):
        int_id = next_int_id + i
        composed_id = f"{prefix}:{int_id}"
        new_rows.append(
            {
                "composed_id": composed_id,
                "fqn": fqn,
                "int_id": int_id,
                "status": "active",
                "row_hash": _hash_row(composed_id, fqn),
            }
        )

    updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    return updated, len(new_rows)


def validate_immutability(old: pd.DataFrame, new: pd.DataFrame) -> None:
    """
    Asserts that no pre-existing row had its immutable fields (fqn, int_id, row_hash) changed.
    Raises RegistryIntegrityException on any violation.
    """
    if old.empty:
        return

    merged = old.merge(new, on="composed_id", suffixes=("_old", "_new"))
    for col in ("fqn", "int_id", "row_hash"):
        mismatched = merged[merged[f"{col}_old"] != merged[f"{col}_new"]]
        if not mismatched.empty:
            bad_ids = mismatched["composed_id"].tolist()
            raise RegistryIntegrityException(f"Immutable field '{col}' was modified for: {bad_ids}")


def to_jsonld(df: pd.DataFrame, config: NamespacesConfig) -> dict:
    """Converts the registry DataFrame to a JSON-LD document."""
    context: dict[str, str] = {config.namespace.prefix: config.namespace.uri}
    context.update({prefix: ns.uri for prefix, ns in config.imports.items()})
    graph = df[["composed_id", "fqn", "status"]].rename(columns={"composed_id": "@id"}).to_dict(orient="records")
    return {"@context": context, "@graph": graph}


def write_jsonld(data: dict, path: Path) -> None:
    """Writes a JSON-LD document to a file."""
    path.write_text(json.dumps(data, indent=2) + "\n")
