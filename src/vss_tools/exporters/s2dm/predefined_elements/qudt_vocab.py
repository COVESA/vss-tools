# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Loader and URI cross-reference index for the QUDT-units GraphQL vocabulary.

The vocabulary (`schema.graphql`) is a release asset published by `s2dm-vocab`. It is not
stored in this repository: on first use it is downloaded from the pinned release
(`QUDT_VOCAB_TAG`), verified against a pinned SHA-256 and cached on disk.

- Cache location: `$VSS_TOOLS_CACHE_DIR` if set, else `$XDG_CACHE_HOME/vss_tools`, else `~/.cache/vss_tools`.
- Offline / air-gapped use: set `VSS_TOOLS_QUDT_VOCAB_DIR` to a directory containing `schema.graphql`;
  nothing is downloaded and the file is used as is.

It declares one GraphQL enum per QUDT quantity kind (e.g. `TemperatureUnit`), annotated with
`@reference(uri: ...)` on both the enum type (quantity-kind IRI) and each enum
value (unit IRI).

This module avoids validating the entire (~500+ enum) file on every
export by using a two-phase approach:

1. Cheap indexing pass (first use): parse the SDL into a `DocumentNode`
   (parsing only, no schema validation) and walk its definitions to build
   URI -> name indices directly from the AST.
2. Lazy realization pass (on demand): only when a specific enum is actually
   needed, build a small `DocumentNode` containing just the `@reference`
   directive definition and that one enum, then call `build_ast_schema()` on
   it to obtain a real `GraphQLEnumType`/`GraphQLDirective`. Results are cached.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from graphql import (
    DirectiveDefinitionNode,
    DirectiveNode,
    DocumentNode,
    EnumTypeDefinitionNode,
    GraphQLDirective,
    GraphQLEnumType,
    parse,
)
from graphql.utilities import build_ast_schema

from vss_tools import log

_REFERENCE_DIRECTIVE_NAME = "reference"
_REFERENCE_ARG_NAME = "uri"

# To update the vocabulary: bump the tag and the SHA-256 shown on the s2dm-vocab release page.
QUDT_VOCAB_NAME = "qudt-units"
QUDT_VOCAB_TAG = "qudt-units-v3.5.2"
QUDT_VOCAB_VERSION = QUDT_VOCAB_TAG
QUDT_VOCAB_SOURCE = "https://github.com/COVESA/s2dm-vocab"
QUDT_VOCAB_ARTIFACT = "schema.graphql"
QUDT_VOCAB_SHA256 = "9f2f334e6ba51f6eb1f31ef099345b4caac2568ce0f598c6e5c42e11a4e1db5e"
QUDT_VOCAB_URL = f"{QUDT_VOCAB_SOURCE}/releases/download/{QUDT_VOCAB_TAG}/{QUDT_VOCAB_ARTIFACT}"

QUDT_VOCAB_DIR_ENV = "VSS_TOOLS_QUDT_VOCAB_DIR"
CACHE_DIR_ENV = "VSS_TOOLS_CACHE_DIR"
_DOWNLOAD_TIMEOUT_SECONDS = 60


class UnresolvedQudtUnitError(ValueError):
    """Raised when a VSS unit's declared QUDT URI(s) cannot be found in the QUDT vocabulary."""


class QudtVocabDownloadError(RuntimeError):
    """Raised when the QUDT vocabulary cannot be downloaded or fails checksum verification."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cache_root() -> Path:
    override = os.environ.get(CACHE_DIR_ENV)
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CACHE_HOME")
    return (Path(xdg) if xdg else Path.home() / ".cache") / "vss_tools"


def _download_schema(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    try:
        with urllib.request.urlopen(QUDT_VOCAB_URL, timeout=_DOWNLOAD_TIMEOUT_SECONDS) as response:  # noqa: S310
            tmp.write_bytes(response.read())
        actual = _sha256(tmp)
        if actual != QUDT_VOCAB_SHA256:
            raise QudtVocabDownloadError(
                f"Checksum mismatch for '{QUDT_VOCAB_URL}': expected {QUDT_VOCAB_SHA256}, got {actual}."
            )
        tmp.replace(target)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise QudtVocabDownloadError(
            f"Could not download the QUDT vocabulary from '{QUDT_VOCAB_URL}': {exc}. "
            f"If you are offline, download the file manually and set {QUDT_VOCAB_DIR_ENV} to the "
            f"directory containing '{QUDT_VOCAB_ARTIFACT}'."
        ) from exc
    finally:
        tmp.unlink(missing_ok=True)


def get_schema_path() -> Path:
    """Return the local path of the QUDT vocabulary schema, downloading and caching it if needed."""
    override = os.environ.get(QUDT_VOCAB_DIR_ENV)
    if override:
        path = Path(override) / QUDT_VOCAB_ARTIFACT
        if not path.is_file():
            raise QudtVocabDownloadError(f"{QUDT_VOCAB_DIR_ENV} is set but '{path}' does not exist.")
        return path

    path = _cache_root() / QUDT_VOCAB_NAME / QUDT_VOCAB_TAG / QUDT_VOCAB_ARTIFACT
    if not (path.is_file() and _sha256(path) == QUDT_VOCAB_SHA256):
        _download_schema(path)
    return path


def _get_reference_uri(directives: tuple[DirectiveNode, ...]) -> str | None:
    for directive in directives:
        if directive.name.value != _REFERENCE_DIRECTIVE_NAME:
            continue
        for arg in directive.arguments:
            if arg.name.value == _REFERENCE_ARG_NAME and hasattr(arg.value, "value"):
                return str(arg.value.value)  # type: ignore[attr-defined]
    return None


@dataclass(frozen=True)
class _VocabIndex:
    reference_directive_definition: DirectiveDefinitionNode
    enum_definitions: dict[str, EnumTypeDefinitionNode]
    # enum_type_name -> {unit IRI -> enum_value_name}. Scoped per enum because the *same*
    # unit IRI (e.g. "unit/DEG_C") legitimately appears in many different quantity-kind
    # enums (TemperatureUnit, WetBulbTemperatureUnit, DewPointTemperatureUnit, ...), so a
    # flat, global unit-IRI index would be ambiguous.
    enum_unit_uri_index: dict[str, dict[str, str]]
    quantity_kind_uri_index: dict[str, str]  # quantity-kind IRI -> enum_type_name


def _build_index() -> _VocabIndex:
    schema_path = get_schema_path()
    source = schema_path.read_text(encoding="utf-8")
    document = parse(source)

    reference_directive_definition: DirectiveDefinitionNode | None = None
    enum_definitions: dict[str, EnumTypeDefinitionNode] = {}
    enum_unit_uri_index: dict[str, dict[str, str]] = {}
    quantity_kind_uri_index: dict[str, str] = {}

    for definition in document.definitions:
        if isinstance(definition, DirectiveDefinitionNode) and definition.name.value == _REFERENCE_DIRECTIVE_NAME:
            reference_directive_definition = definition
        elif isinstance(definition, EnumTypeDefinitionNode):
            enum_type_name = definition.name.value
            enum_definitions[enum_type_name] = definition

            quantity_kind_uri = _get_reference_uri(definition.directives)
            if quantity_kind_uri:
                quantity_kind_uri_index[quantity_kind_uri] = enum_type_name

            unit_uri_map: dict[str, str] = {}
            for value_node in definition.values or ():
                unit_uri = _get_reference_uri(value_node.directives)
                if unit_uri:
                    unit_uri_map[unit_uri] = value_node.name.value
            enum_unit_uri_index[enum_type_name] = unit_uri_map

    if reference_directive_definition is None:
        raise UnresolvedQudtUnitError(
            f"QUDT vocabulary at '{schema_path}' does not declare the '@{_REFERENCE_DIRECTIVE_NAME}' directive."
        )

    return _VocabIndex(
        reference_directive_definition=reference_directive_definition,
        enum_definitions=enum_definitions,
        enum_unit_uri_index=enum_unit_uri_index,
        quantity_kind_uri_index=quantity_kind_uri_index,
    )


_index: _VocabIndex | None = None


def _get_index() -> _VocabIndex:
    global _index
    if _index is None:
        _index = _build_index()
    return _index


_QUERY_STUB_DEFINITIONS = parse("type Query { _empty: String }").definitions

_reference_directive: GraphQLDirective | None = None
_enum_type_cache: dict[str, GraphQLEnumType] = {}


def get_reference_directive() -> GraphQLDirective:
    """Return the real `@reference` directive, realized (and cached) from the vendored AST."""
    global _reference_directive
    if _reference_directive is None:
        index = _get_index()
        document = DocumentNode(definitions=(index.reference_directive_definition, *_QUERY_STUB_DEFINITIONS))
        schema = build_ast_schema(document)
        directive = schema.get_directive(_REFERENCE_DIRECTIVE_NAME)
        assert directive is not None
        _reference_directive = directive
    return _reference_directive


def get_enum_type(enum_type_name: str) -> GraphQLEnumType:
    """Return the real, vendored `GraphQLEnumType` for the given enum type name (cached, lazy)."""
    cached = _enum_type_cache.get(enum_type_name)
    if cached is not None:
        return cached

    index = _get_index()
    enum_definition = index.enum_definitions.get(enum_type_name)
    if enum_definition is None:
        raise UnresolvedQudtUnitError(f"Unknown QUDT-vocab enum type '{enum_type_name}'.")

    document = DocumentNode(
        definitions=(index.reference_directive_definition, enum_definition, *_QUERY_STUB_DEFINITIONS)
    )
    schema = build_ast_schema(document)
    enum_type = schema.type_map[enum_type_name]
    assert isinstance(enum_type, GraphQLEnumType)
    _enum_type_cache[enum_type_name] = enum_type
    return enum_type


def get_quantity_kind_uri(enum_type_name: str) -> str | None:
    """Return the quantity-kind IRI declared on the vendored enum type itself (its own `@reference`), if any."""
    index = _get_index()
    for quantity_kind_uri, name in index.quantity_kind_uri_index.items():
        if name == enum_type_name:
            return quantity_kind_uri
    return None


def get_unit_uris(enum_type_name: str) -> dict[str, str]:
    """Return {enum_value_name -> unit IRI} for every value declared in the vendored enum (used or not)."""
    index = _get_index()
    unit_uri_map = index.enum_unit_uri_index.get(enum_type_name, {})
    return {enum_value_name: uri for uri, enum_value_name in unit_uri_map.items()}


def _suggest_quantity_kind_uris(quantity_kind_uri: str, index: _VocabIndex) -> list[str]:
    return difflib.get_close_matches(quantity_kind_uri, list(index.quantity_kind_uri_index.keys()), n=3, cutoff=0.5)


def _suggest_unit_uris(unit_uri: str, candidates: list[str]) -> list[str]:
    return difflib.get_close_matches(unit_uri, candidates, n=3, cutoff=0.5)


_QUDT_HTTPS_PREFIX = "https://qudt.org/"
_QUDT_HTTP_PREFIX = "http://qudt.org/"


def _lookup_with_http_fallback(uri: str, candidates: dict[str, str], vss_key: str) -> str | None:
    """Look up `uri`; if absent and it is a `https://qudt.org/` URI, retry with `http://qudt.org/`.

    The vendored vocabulary uses `http://` IRIs, while users commonly write the `https://` form.
    """
    value = candidates.get(uri)
    if value is None and uri.startswith(_QUDT_HTTPS_PREFIX):
        fallback_uri = _QUDT_HTTP_PREFIX + uri[len(_QUDT_HTTPS_PREFIX) :]
        value = candidates.get(fallback_uri)
        if value is not None:
            log.warning(
                f"VSS unit '{vss_key}': QUDT URI '{uri}' was not found as is; resolved it as '{fallback_uri}'. "
                "Consider using the 'http://' form in the units file."
            )
    return value


def resolve_qudt_unit_uri(*, unit_uri: str, quantity_kind_uri: str, vss_key: str) -> tuple[str, str]:
    """Resolve a native `qudt:` unit/quantity-kind URI pair against the vendored vocabulary.

    The quantity-kind URI selects the enum (one enum per quantity kind); the unit URI is then
    looked up among *that* enum's own values. Unit URIs are not globally unique in QUDT (e.g.
    "unit/DEG_C" is a valid value of many different quantity-kind enums), so the unit URI is
    always resolved relative to the enum selected by the quantity-kind URI.

    Returns:
        (enum_type_name, enum_value_name)

    Raises:
        UnresolvedQudtUnitError: if the quantity-kind URI or the unit URI (within that
            quantity kind's enum) cannot be found in the vendored vocabulary, with
            closest-match suggestions included where possible.
    """
    index = _get_index()

    enum_type_name = _lookup_with_http_fallback(quantity_kind_uri, index.quantity_kind_uri_index, vss_key)
    if enum_type_name is None:
        message = (
            f"VSS unit '{vss_key}' declares qudt.quantity-kind URI '{quantity_kind_uri}', which was not "
            f"found in the QUDT vocabulary ({QUDT_VOCAB_NAME}@{QUDT_VOCAB_VERSION})."
        )
        suggestions = _suggest_quantity_kind_uris(quantity_kind_uri, index)
        if suggestions:
            message += " Closest matches: " + ", ".join(suggestions) + "."
        raise UnresolvedQudtUnitError(message)

    unit_uri_map = index.enum_unit_uri_index.get(enum_type_name, {})
    enum_value_name = _lookup_with_http_fallback(unit_uri, unit_uri_map, vss_key)
    if enum_value_name is None:
        message = (
            f"VSS unit '{vss_key}' declares qudt.unit URI '{unit_uri}', which was not found among the "
            f"values of enum '{enum_type_name}' (quantity-kind '{quantity_kind_uri}') in the "
            f"QUDT vocabulary ({QUDT_VOCAB_NAME}@{QUDT_VOCAB_VERSION})."
        )
        suggestions = _suggest_unit_uris(unit_uri, list(unit_uri_map.keys()))
        if suggestions:
            message += " Closest matches: " + ", ".join(suggestions) + "."
        raise UnresolvedQudtUnitError(message)

    return enum_type_name, enum_value_name
