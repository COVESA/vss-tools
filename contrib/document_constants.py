#!/usr/bin/env python3

#
# (C) 2021 ProFUSION Sistemas e Solucoes LTDA
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import argparse
import sys
from enum import Enum
from textwrap import dedent
from typing import Mapping, Sequence, Type, Union

import vspec.model.constants as constants


# NOTE: only used to fetch the auto-generated __doc__
class GenericEnum(Enum):
    placeholder = 1


def create_table(
    header: Sequence[str],
    rows: Sequence[Sequence[str]],
    size_rounding: int = 4,
):
    """Generate markdown table

    It will measure all the row cells and their header to generate
    a human friendly table (the text representation looks like a table).

    To avoid too much resizing when the cells change, the sizes are rounded
    using `size_rounding`.
    """
    def round(n):
        remainder = n % size_rounding
        if not remainder:
            return n
        return n + remainder

    max_lengths = [round(len(h)) for h in header]
    count = len(max_lengths)
    for r in rows:
        for i in range(count):
            max_lengths[i] = max(max_lengths[i], round(len(r[i])))

    fmt = "|"
    for ml in max_lengths:
        fmt += f" %-{ml}s |"

    ret = [
        fmt % header,
        "|" + "|".join(f":{'-' * n}-" for n in max_lengths) + "|",
    ]
    for r in rows:
        ret.append(fmt % r)
    return "\n".join(ret)


class DocumentEnum:
    kind = Enum
    cls: Enum
    table_header = ("Symbol", "Value")

    def __init__(self, cls: Enum) -> None:
        self.cls = cls

    @property
    def name(self):
        return self.cls.__name__

    def __str__(self) -> str:
        lines = []
        if self.cls.__doc__ and self.cls.__doc__ != GenericEnum.__doc__:
            doc = self.cls.__doc__.splitlines()
            if len(doc) > 2 and doc[0] and not doc[1]:
                lines.append(f"## {self.name} ({doc[0].strip()})")
                doc.pop(0)
                doc.pop(0)
            else:
                lines.append(f"## {self.name}")

            lines.append(dedent("\n".join(doc)))
            lines.append("")
        else:
            lines.append(f"## {self.name}")

        rows = [
            (f"`{m.name}`", m.value) for m in self.cls.__members__.values()
        ]
        lines.append(create_table(self.table_header, rows))
        lines.append("")
        return "\n".join(lines)


DocumentGenerators = Union[Type[DocumentEnum]]
Documents = Union[DocumentEnum]
collect_map: Mapping[str, DocumentGenerators] = {
    "Enumerations": DocumentEnum,
}


def collect() -> Mapping[str, Sequence[Documents]]:
    collected = {}
    for name in constants.__all__:
        element = getattr(constants, name)
        for key, doc in collect_map.items():
            if issubclass(element, doc.kind):
                collected.setdefault(key, []).append(doc(element))
    return collected


def get_args() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Generate MarkDown documentation based on code constants"
    )
    ap.add_argument(
        "--kind", "-k",
        help="If provided, restrict kind of constants to document.",
        choices=tuple(collect_map.keys()),
    )
    ap.add_argument(
        "--name", "-n",
        help="If provided, restrict the name of constant to document.",
    )
    ap.add_argument(
        "--output-file", "-o",
        help="File to write (defaults to stdout)",
        type=argparse.FileType("w"),
        default=sys.stdout,
    )
    return ap


def main():
    ap = get_args()
    args = ap.parse_args()

    out = args.output_file
    collected = collect()
    for key, docs in collected.items():
        if args.kind and args.kind != key:
            continue
        out.write(f"# {key}\n")
        for d in docs:
            if args.name and args.name != d.name:
                continue
            out.write(str(d))
            out.write("\n")


if __name__ == "__main__":
    main()
