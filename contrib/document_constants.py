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
from typing import Callable, List, Sequence

import vspec.model.constants as constants


# NOTE: only used to fetch the auto-generated __doc__
class GenericEnum(Enum):
    placeholder = 1


def get_max_values(a: Sequence[int], b: Sequence[int]) -> Sequence[int]:
    """Given two sequences, get a sequence with the maximum of each position:

    >>> get_max_values([0, 1, 2], [10, 20, 30])
    [10, 20, 30]
    """
    return [max(a[i], b[i]) for i in range(len(a))]


def measure_items(
    items: Sequence[str],
    measure: Callable[[str], int],
) -> Sequence[int]:
    """Returns a sequence of the measurement for each item in the input:

    >>> measure_items(['a', 'banana'], len)
    [1, 6]
    >>> measure_items(['a', 'banana'], lambda text: len(text) * 10)
    [10, 60]
    """
    return [measure(c) for c in items]


def get_max_columns_lengths(
    rows: Sequence[Sequence[str]],
    columns_count: int,
    measure: Callable[[str], int]
) -> Sequence[int]:
    """Returns the maximum lengths for each column given the rows:

    >>> get_max_columns_lengths(
    ...    [['a', 'b', 'cccccccccc'],
    ...     ['apple', 'banana', 'coconut']],
    ...    3,
    ...    len)
    [5, 6, 10]
    """
    max_lengths = [0] * columns_count
    for r in rows:
        row_lengths = measure_items(r, measure)
        max_lengths = get_max_values(max_lengths, row_lengths)
    return max_lengths


def create_rounded_str_len(size_rounding: int) -> Callable[[str], int]:
    """Returns a measurement function that rounds to multiple of given sizes:

    >>> measure4 = create_rounded_str_len(4)
    >>> measure4('a')
    4
    >>> measure4('abcd')
    4
    >>> measure4('abcde')
    8

    >>> measure3 = create_rounded_str_len(3)
    >>> measure3('a')
    3
    >>> measure3('abcd')
    6
    >>> measure3('abcde')
    6
    """
    def measure(text: str):
        n = len(text)
        remainder = n % size_rounding
        if not remainder:
            return n
        return n + size_rounding - remainder
    return measure


def create_table_format(lengths: Sequence[int]) -> str:
    """Returns the Python-format to left-align the columns:

    >>> create_table_format([4, 8])
    '| %-4s | %-8s |'
    >>> create_table_format([4, 8, 12])
    '| %-4s | %-8s | %-12s |'
    """
    fmt = "|"
    for length in lengths:
        fmt += f" %-{length}s |"
    return fmt


def create_table_header_separator(lengths: Sequence[str]) -> str:
    """Returns the Markdown table separator the columns:

    >>> create_table_header_separator([4, 8])
    '|:-----|:---------|'
    >>> create_table_header_separator([4, 8, 12])
    '|:-----|:---------|:-------------|'
    """
    fmt = "|"
    for length in lengths:
        dashes = '-' * length
        fmt += f":{dashes}-|"
    return fmt


def create_table(
    header: Sequence[str],
    rows: Sequence[Sequence[str]],
    size_rounding: int = 4,
    omit_empty_columns: bool = True,
):
    """Generate markdown table

    It will measure all the row cells and their header to generate
    a human friendly table (the text representation looks like a table).

    To avoid too much resizing when the cells change, the sizes are rounded
    using `size_rounding`.

    Example:
    >>> print(create_table(
    ...   ['key', 'value'],
    ...   [['a', '1'], ['longer key here', '123456']],
    ...   4))
    | key              | value    |
    |:-----------------|:---------|
    | a                | 1        |
    | longer key here  | 123456   |

    Columns with values will be omitted by default:
    >>> print(create_table(
    ...   ['key', 'value', 'nothing'],
    ...   [['a', '1', ''], ['longer key here', '123456', '']],
    ...   4))
    | key              | value    |
    |:-----------------|:---------|
    | a                | 1        |
    | longer key here  | 123456   |

    One can force them to be displayed regardless:
    >>> print(create_table(
    ...   ['key', 'value', 'nothing'],
    ...   [['a', '1', ''], ['longer key here', '123456', '']],
    ...   4, False))
    | key              | value    | nothing  |
    |:-----------------|:---------|:---------|
    | a                | 1        |          |
    | longer key here  | 123456   |          |
    """
    measure = create_rounded_str_len(size_rounding)
    max_lengths = get_max_columns_lengths(
        rows,
        len(header),
        measure,
    )
    if not omit_empty_columns:
        def filter_visible_columns(seq):
            return tuple(seq)
    else:
        visible_columns = [bool(ml) for ml in max_lengths]
        def filter_visible_columns(seq):
            return tuple(x for i, x in enumerate(seq) if visible_columns[i])

    max_lengths = get_max_values(
        max_lengths,
        measure_items(header, measure),
    )

    visible_columns_lengths = filter_visible_columns(max_lengths)
    fmt = create_table_format(visible_columns_lengths)
    ret = [
        fmt % filter_visible_columns(header),
        create_table_header_separator(visible_columns_lengths),
    ]
    for r in rows:
        ret.append(fmt % filter_visible_columns(r))
    return "\n".join(ret)


class DocumentEnum:
    cls: Enum
    table_header = ("Symbol", "Value", "Domain", "Description")

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

        rows = []
        for m in self.cls.__members__.values():
            v = m.value
            if isinstance(v, constants.VSSConstant):
                rows.append((f"`{m.name}`", v, v.domain, v.description))
            else:
                rows.append((f"`{m.name}`", v, '', ''))

        lines.append(create_table(self.table_header, rows))
        lines.append("")
        return "\n".join(lines)



def collect() -> Sequence[DocumentEnum]:
    collected: List[DocumentEnum] = []
    for name in constants.__all__:
        element = getattr(constants, name)
        if issubclass(element, Enum):
            collected.append(DocumentEnum(element))
    return collected


def get_args() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Generate MarkDown documentation based on code constants"
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
    for doc in collected:
        if args.name and args.name != doc.name:
            continue
        out.write(str(doc))
        out.write("\n")


if __name__ == "__main__":
    main()
