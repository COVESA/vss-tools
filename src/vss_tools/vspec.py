# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from vss_tools import log


class IncludeStatementException(Exception):
    pass


class IncludeNotFoundException(Exception):
    pass


class InvalidSpecDuplicatedEntryException(Exception):
    pass


class SpecException(Exception):
    pass


class Include:
    def __init__(self, statement: str, prefix: str | None = None):
        self.statement = statement
        split = statement.split()
        if len(split) < 2:
            raise IncludeStatementException(f"Malformed include statement: {statement}")
        self.target = split[1]
        self.prefix = prefix
        if len(split) == 3:
            if self.prefix is not None:
                self.prefix += f".{split[2]}"
            else:
                self.prefix = split[2]

    def resolve_path(self, include_dirs: list[Path]) -> Path:
        for dir in include_dirs:
            path = dir / self.target
            if path.exists():
                log.debug(f"'{self.statement}', resolved={path}")
                return path
        raise IncludeNotFoundException(f"Unable to find include {self.target}. Include dirs: {include_dirs}")


def deep_update(base: dict[str, Any], update: dict[str, Any]) -> None:
    for key, value in update.items():
        if isinstance(value, dict):
            if key in base and isinstance(base[key], dict):
                deep_update(base[key], value)
            else:
                base[key] = value
        else:
            base[key] = value


class VSpec:
    def __init__(
        self,
        source: Path,
        prefix: str | None = None,
    ):
        self.source = source
        self.prefix = prefix

        content = source.read_text()

        self.data = yaml.safe_load(content)
        if self.data is None:
            self.data = {}

        if prefix:
            tmp_data = {}
            for k, v in self.data.items():
                new_key = f"{prefix}.{k}"
                tmp_data[new_key] = v
            self.data = tmp_data

        lines = content.splitlines()
        include_statements = [line.strip() for line in lines if line.strip().startswith("#include")]
        self.includes = [Include(statement, prefix) for statement in include_statements]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}, src={self.source}, prefix={self.prefix}, includes={len(self.includes)}"

    def update(self, other: VSpec) -> None:
        deep_update(self.data, other.data)


def get_vspecs(includes: list[Path], spec: Path, prefix: str | None = None) -> list[VSpec]:
    vspecs: list[VSpec] = []
    vspec = VSpec(spec, prefix)
    vspecs.append(vspec)

    for include in vspec.includes:
        include_spec = include.resolve_path(includes + [vspec.source.parent])
        vspecs.extend(get_vspecs(includes, include_spec, include.prefix))

    return vspecs


def load_vspec(include_dirs: list[Path], specs: list[Path], identifier: str | None = None) -> VSpec:
    spec = None
    vspecs: list[VSpec] = []
    for s in specs:
        includes = [s.parent] + include_dirs
        vspecs.extend(get_vspecs(includes, s))
    pre = "VSpecs"
    if identifier:
        pre += f" ({identifier})"
    log.info(f"{pre} loaded, amount={len(vspecs)}")
    for vspec in vspecs:
        log.debug(vspec)
        if spec is None:
            spec = vspec
        else:
            spec.update(vspec)
    if not spec:
        msg = f"Weird behavior. Could not load any spec: {specs}"
        log.error(msg)
        raise SpecException(msg)
    return spec
