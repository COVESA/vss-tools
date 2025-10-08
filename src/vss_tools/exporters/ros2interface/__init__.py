# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
"""
ROS 2 .msg &.srv exporter for vss-tools (VSS-based), extended with:
- **Topic/Signal filtering** so anyone can export only specific topics.

What it does
------------
* Loads a VSS tree using vss_tools.main.get_trees().
* Traverses leaf signals (sensor/actuator/attribute/property) from the VSS tree.
* Generates:
  - ROS 2 .msg files (either per-leaf or aggregated per direct parent branch).
* Adds VSS metadata (description/unit/min/max/allowed) as comments in .msg and .srv.

New topic filtering
-------------------
Use these options to export only the topics which are needed:
  --topics               (repeatable include patterns)
  --exclude-topics       (repeatable exclude patterns)
  --topics-file          (file with one pattern per line; supports '#'-comments)
  --topics-case-insensitive / --topics-case-sensitive

Patterns can be specified as:
  - Exact FQN:           Vehicle.Speed
  - Leaf name:           Speed
  - Glob:                Vehicle.*.Speed   or   *.Speed
  - Explicit prefix:     glob:*.Speed ,  fqn:Vehicle.Speed ,  name:Speed

Key CLI options (existing remain)
---------------------------------
--mode aggregate|leaf
--srv none|get|set|both
--srv-use-msg / --no-srv-use-msg

Examples
--------
# Export only Vehicle.Speed as leaf message + get/set services:
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_speed_interfaces \
  --mode leaf \
  --srv both --srv-use-msg \
  --topics Vehicle.Speed

# Export all *.Speed signals, aggregated by their parent branches:
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_speed_agg \
  --mode aggregate \
  --srv get \
  --topics '*.Speed'
"""

from __future__ import annotations

import re
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log

# -------------------- VSS loading (stable loader used by vss-tools CLI) --------------------
from vss_tools.main import get_trees  # stable API used by CLI
from vss_tools.tree import VSSNode  # type: ignore


def load_vspec_tree(
    vspec_file: Path,
    include_dirs: Tuple[Path, ...],
    units_files: Tuple[Path, ...],
    quantities_files: Tuple[Path, ...],
    types_files: Tuple[Path, ...],
    overlays_files: Tuple[Path, ...],
    expand: bool,
) -> VSSNode:
    root, _ = get_trees(
        vspec=vspec_file,
        include_dirs=include_dirs,
        quantities=quantities_files,
        units=units_files,
        types=types_files,
        overlays=overlays_files,
        expand=expand,
    )
    return root


# ------------------------------ Naming & type mapping --------------------------------------
ROS_PRIMITIVE_MAP: Dict[str, str] = {
    "boolean": "bool",
    "int8": "int8",
    "uint8": "uint8",
    "int16": "int16",
    "uint16": "uint16",
    "int32": "int32",
    "uint32": "uint32",
    "int64": "int64",
    "uint64": "uint64",
    "float": "float32",
    "double": "float64",
    "string": "string",
}


def to_snake(name: str) -> str:
    # PascalCase -> snake_case, hyphens/spaces -> underscores, collapse
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s.lower()


def to_pascal(name: str) -> str:
    parts = re.split(r"[^0-9a-zA-Z]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def fqn_to_msg_basename(fqn: str) -> str:
    return to_pascal(fqn.replace(".", "_"))


def field_name_from_tail(tail: str) -> str:
    return to_snake(tail)


def map_vss_to_ros_field(datatype: str, arraysize: Optional[int]) -> str:
    base = datatype.strip()
    is_var_array = base.endswith("[]")
    base = base[:-2] if is_var_array else base

    ros_base = ROS_PRIMITIVE_MAP[base]

    if arraysize and arraysize > 0:
        return f"{ros_base}[{arraysize}]"
    if is_var_array:
        return f"{ros_base}[]"
    return ros_base


# ------------------------------------- Tree traversal --------------------------------------
LEAF_TYPES = {"sensor", "actuator", "attribute", "property"}


def iter_leaves(root: VSSNode) -> Iterable[Tuple[VSSNode, object]]:
    stack = [root]
    while stack:
        node = stack.pop()
        children = getattr(node, "children", None) or []
        if children:
            stack.extend(children)
        data = node.get_vss_data()
        ntype = getattr(data, "type", None)
        if ntype in LEAF_TYPES:
            yield node, data


def direct_parent_fqn(node: VSSNode) -> str:
    fqn = node.get_fqn()
    parts = fqn.split(".")
    if len(parts) <= 1:
        return parts[0]
    return ".".join(parts[:-1])


# ------------------------------------ Topic filtering ---------------------------------------
# Pattern rule compiler with flexible syntax:
#   - 'regex:<pattern>'  -> regex against FQN or leaf tail
#   - 'glob:<pattern>'   -> fnmatch glob against FQN or tail
#   - 'fqn:<value>'      -> exact FQN or prefix (FQN == value OR FQN startswith value+'.')
#   - 'name:<value>'     -> tail name equality (or glob if contains * or ?)
#   - implicit:
#       contains * or ?  -> treat as glob
#       contains '.'     -> treat as fqn
#       otherwise        -> treat as name
Rule = Callable[[str, str], bool]  # (tail, fqn) -> bool


def _compile_rule(pattern: str, case_insensitive: bool) -> Rule:
    kind: Optional[str] = None
    pat = pattern

    if ":" in pattern:
        k, v = pattern.split(":", 1)
        if k in {"regex", "glob", "fqn", "name"}:
            kind, pat = k, v

    if kind is None:
        if any(ch in pattern for ch in "*?"):
            kind = "glob"
        elif "." in pattern:
            kind = "fqn"
        else:
            kind = "name"

    if case_insensitive:
        pat_ci = pat.lower()

    if kind == "regex":
        flags = re.I if case_insensitive else 0
        rx = re.compile(pat, flags)
        return lambda tail, fqn: bool(rx.search(fqn)) or bool(rx.fullmatch(tail))

    if kind == "glob":

        def _g(tail: str, fqn: str) -> bool:
            target_fqn = fqn.lower() if case_insensitive else fqn
            target_tail = tail.lower() if case_insensitive else tail
            p = pat_ci if case_insensitive else pat
            return fnmatchcase(target_fqn, p) or fnmatchcase(target_tail, p)

        return _g

    if kind == "fqn":

        def _f(tail: str, fqn: str) -> bool:
            tf = fqn.lower() if case_insensitive else fqn
            p = pat_ci if case_insensitive else pat
            return tf == p or tf.startswith(p + ".")

        return _f

    # name
    def _n(tail: str, fqn: str) -> bool:
        tt = tail.lower() if case_insensitive else tail
        if "*" in pat or "?" in pat:
            p = pat_ci if case_insensitive else pat
            return fnmatchcase(tt, p)
        p = pat_ci if case_insensitive else pat
        return tt == p

    return _n


class TopicMatcher:
    def __init__(
        self,
        include_patterns: Sequence[str],
        exclude_patterns: Sequence[str],
        case_insensitive: bool = False,
    ):
        self.include_rules: List[Rule] = (
            [_compile_rule(p, case_insensitive) for p in include_patterns]
            if include_patterns
            else [lambda tail, fqn: True]  # match all if no includes
        )
        self.exclude_rules: List[Rule] = [_compile_rule(p, case_insensitive) for p in exclude_patterns]

    def matches(self, fqn: str) -> bool:
        tail = fqn.split(".")[-1]
        if any(rule(tail, fqn) for rule in self.exclude_rules):
            return False
        return any(rule(tail, fqn) for rule in self.include_rules)


def _read_patterns_file(path: Optional[Path]) -> List[str]:
    if not path:
        return []
    patterns: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        patterns.append(s)
    return patterns


def filter_leaves(
    all_leaves: Iterable[Tuple[VSSNode, object]],
    include_patterns: Sequence[str],
    exclude_patterns: Sequence[str],
    case_insensitive: bool,
) -> List[Tuple[VSSNode, object]]:
    matcher = TopicMatcher(include_patterns, exclude_patterns, case_insensitive)
    selected: List[Tuple[VSSNode, object]] = []

    for node, data in all_leaves:
        fqn = node.get_fqn()
        if matcher.matches(fqn):
            selected.append((node, data))
    return selected


# ------------------------------------- Rendering helpers -----------------------------------
def _format_comment(lines: List[str]) -> str:
    lines = [f"# {ln}" if ln else "#" for ln in lines]
    return "\n".join(lines) + ("\n" if lines else "")


def render_msg_file(
    fqn: str,
    fields: List[Dict[str, str]],
    header_comment: List[str],
    enum_comment: Optional[List[str]] = None,
) -> str:
    buf: List[str] = []
    buf.append("# Auto-generated from VSS by vss-tools (ros2msg exporter)")
    if header_comment:
        buf.append(_format_comment(header_comment).rstrip())
    if enum_comment:
        buf.append(_format_comment(enum_comment).rstrip())

    for f in fields:
        buf.append("")
        line = f"{f['type']} {f['name']}"
        if f.get("comment"):
            comment = f"# {f['comment']}"
            buf.append(comment)
        buf.append(line)
    buf.append("")
    return "\n".join(buf)


def render_srv_file(
    request_lines: List[str],
    response_lines: List[str],
    header: Optional[List[str]] = None,
) -> str:
    buf: List[str] = []
    buf.append("# Auto-generated from VSS by vss-tools (ros2msg exporter)")
    if header:
        buf.append(_format_comment(header).rstrip())
    buf.extend(request_lines if request_lines else [])
    buf.append("---")
    buf.extend(response_lines if response_lines else [])
    buf.append("")
    return "\n".join(buf)


# ----------------------------- Build fields & msgs ------------------------------


def build_field_from_leaf(leaf_node: VSSNode, data) -> Dict[str, str]:
    fqn = leaf_node.get_fqn()
    tail = fqn.split(".")[-1]
    name = field_name_from_tail(tail)
    vss_dt = getattr(data, "datatype", "string")
    arraysize = getattr(data, "arraysize", None)
    ros_type = map_vss_to_ros_field(vss_dt, arraysize)
    unit = getattr(data, "unit", None)
    minv = getattr(data, "min", None)
    maxv = getattr(data, "max", None)
    desc = getattr(data, "description", None)

    extra: List[str] = []
    if unit:
        extra.append(f"unit={unit}")
    rng: List[str] = []
    if minv is not None:
        rng.append(str(minv))
    if maxv is not None:
        rng.append(str(maxv))
    if rng:
        extra.append("range=[" + ",".join(rng) + "]")

    comment = "; ".join([p for p in [desc, " ".join(extra) if extra else None] if p])
    return {"type": ros_type, "name": name, "comment": comment}


# ------------------------- Generates msg files with aggregated topics of a parent branch --------------------------


def generate_msgs_aggregate(
    root: VSSNode, preselected: Optional[Sequence[Tuple[VSSNode, object]]] = None
) -> List[Tuple[str, str, List[Dict[str, str]]]]:
    # returns list[(msg_filename, content, fields)]
    items = list(preselected) if preselected is not None else list(iter_leaves(root))
    buckets: Dict[str, List[Tuple[VSSNode, object]]] = {}

    for node, data in items:
        pfqn = direct_parent_fqn(node)
        buckets.setdefault(pfqn, []).append((node, data))

    outputs: List[Tuple[str, str, List[Dict[str, str]]]] = []

    for pfqn, leaf_items in buckets.items():
        fields: List[Dict[str, str]] = [
            build_field_from_leaf(n, d) for n, d in sorted(leaf_items, key=lambda x: x[0].get_fqn())
        ]
        fields = [{"type": "uint64", "name": "timestamp"}] + fields
        header_comment = [f"Parent branch: {pfqn}"]

        allowed_values: List[str] = []

        for _, d in leaf_items:
            vals = getattr(d, "allowed", None)
            if isinstance(vals, (list, tuple)):
                allowed_values.extend(list(vals))
        enum_comment = None
        if allowed_values:
            enum_comment = ["Allowed values (combined): " + ", ".join(map(str, allowed_values))]

        msg_name = fqn_to_msg_basename(pfqn) + ".msg"
        content = render_msg_file(pfqn, fields, header_comment, enum_comment)
        outputs.append((msg_name, content, fields))
    return outputs


# ----------- Generates separate msg files for each leaf node of a parent branch --------------


def generate_msgs_leaf(
    root: VSSNode, preselected: Optional[Sequence[Tuple[VSSNode, object]]] = None
) -> List[Tuple[str, str, List[Dict[str, str]]]]:
    outputs: List[Tuple[str, str, List[Dict[str, str]]]] = []
    items = list(preselected) if preselected is not None else list(iter_leaves(root))

    for node, data in items:
        fqn = node.get_fqn()
        field = build_field_from_leaf(node, data)
        header_comment = [f"Signal: {fqn}"]
        allowed_values = getattr(data, "allowed", None)
        enum_comment = None
        if isinstance(allowed_values, (list, tuple)) and allowed_values:
            enum_comment = ["Allowed values: " + ", ".join(map(str, list(allowed_values)))]
        msg_name = fqn_to_msg_basename(fqn) + ".msg"
        base_fields = [{"type": "uint64", "name": "timestamp"}, field]
        content = render_msg_file(fqn, base_fields, header_comment, enum_comment)
        outputs.append((msg_name, content, base_fields))
        # content = render_msg_file(fqn, [field], header_comment, enum_comment)
        # outputs.append((msg_name, content, [field]))
    return outputs


# ------------------------- SRV generation --------------------------
def srv_names_for_msg(msg_filename: str) -> Tuple[str, str, str, str]:
    base = msg_filename[:-4] if msg_filename.lower().endswith(".msg") else msg_filename
    return base, f"Get{base}.srv", f"Set{base}.srv", f"Get{base}ByTime.srv"


def render_get_srv(pkg_name: str, msg_name: str, fields: List[Dict[str, str]], use_msg: bool) -> str:
    header = [f"Service: Get{msg_name}", "Returns latest values for this group."]
    request = [
        "uint64 start_time_ms",
        "uint64 end_time_ms",
    ]
    if use_msg:
        response = [f"{msg_name}[] data"]
    else:
        response = [f"{f['type']} {f['name']} # {f.get('comment', '')}".rstrip() for f in fields]
    return render_srv_file(request, response, header)


def render_set_srv(pkg_name: str, msg_name: str, fields: List[Dict[str, str]], use_msg: bool) -> str:
    header = [f"Service: Set{msg_name}", "Sets values for this group."]
    if use_msg:
        request = [f"{msg_name} data"]
    else:
        request = [f"{f['type']} {f['name']} # {f.get('comment', '')}".rstrip() for f in fields]
    response = ["bool success", "string message"]
    return render_srv_file(request, response, header)


# ---------------------------------------------- CLI ----------------------------------------


@click.command(help="Export a VSS model to a ROS 2 interface package (.msg + optional .srv).")
@clo.vspec_opt
@clo.include_dirs_opt
@clo.units_opt
@clo.quantities_opt
@clo.types_opt
@clo.overlays_opt
@clo.expand_opt
@click.option(
    "--output",
    type=click.Path(dir_okay=True, path_type=Path, file_okay=False),
    help="Output Directory.",
    required=True,
)
@click.option(
    "--package-name",
    required=True,
    default="vss_interfaces",
    help="Name of the ROS 2 interface package to generate (e.g., vss_interfaces).",
)
@click.option(
    "--mode",
    type=click.Choice(["aggregate", "leaf"], case_sensitive=False),
    default="aggregate",
    show_default=True,
    help="Aggregate leaves by direct parent branch, or generate one .msg per leaf.",
)
@click.option(
    "--srv",
    type=click.Choice(["none", "get", "set", "both"], case_sensitive=False),
    default="none",
    show_default=True,
    help="Also generate .srv files: Get<Msg>.srv, Set<Msg>.srv, or both.",
)
@click.option(
    "--srv-use-msg/--no-srv-use-msg",
    default=True,
    show_default=True,
    help="Whether services should nest the generated .msg as a field. If disabled, fields are flattened.",
)
@click.option(
    "--topics",
    multiple=True,
    help=(
        "Include patterns for selecting topics/signals. Examples: "
        "'Vehicle.Speed', 'Speed', '*.Speed', 'name:Speed', 'fqn:Vehicle.Speed'. "
        "Repeatable."
    ),
)
@click.option(
    "--exclude-topics",
    multiple=True,
    help=("Exclude patterns (same syntax as --topics). " "Applied after includes; any match here is removed."),
)
@click.option(
    "--topics-file",
    type=click.Path(path_type=Path),
    help="File with one pattern per line (supports comments with '#').",
)
@click.option(
    "--topics-case-insensitive/--topics-case-sensitive",
    default=False,
    show_default=True,
    help="Case-insensitive matching for topic patterns.",
)
def cli(
    vspec: Path,
    include_dirs: Tuple[Path, ...],
    units: Tuple[Path, ...],
    quantities: Tuple[Path, ...],
    types: Tuple[Path, ...],
    overlays: Tuple[Path, ...],
    output: Path,
    expand: bool,
    package_name: str,
    mode: str,
    srv: str,
    srv_use_msg: bool,
    topics: Tuple[str, ...],
    exclude_topics: Tuple[str, ...],
    topics_file: Optional[Path],
    topics_case_insensitive: bool,
):
    # 1) Load VSS
    log.info("Loading VSS…")
    root = load_vspec_tree(
        vspec_file=vspec,
        include_dirs=include_dirs,
        units_files=units,
        quantities_files=quantities,
        types_files=types,
        overlays_files=overlays,
        expand=expand,
    )

    # 2) Gather leaves and apply topic filters (if provided)
    all_leaves = list(iter_leaves(root))

    include_patterns = list(topics) + _read_patterns_file(topics_file)
    exclude_patterns = list(exclude_topics)

    preselected: Optional[List[Tuple[VSSNode, object]]] = None
    if include_patterns or exclude_patterns:
        log.info("Applying topic filters (includes=%d, excludes=%d)…", len(include_patterns), len(exclude_patterns))
        preselected = filter_leaves(
            all_leaves,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            case_insensitive=topics_case_insensitive,
        )
        if not preselected:
            if (include_patterns and len(include_patterns) > 0) or (exclude_patterns and len(exclude_patterns) > 0):
                click.secho(
                    "No VSS signals matched the provided topic filters.\n"
                    "   Please select a topic (e.g., via --topics/--exclude-topics/--topics-file) and try again.",
                    fg="yellow",
                )
            else:
                click.secho(
                    "No topics selected. Please specify --topics/--topics-file if you want to filter.",
                    fg="yellow",
                )

    # 3) Build messages from VSS (optionally using the preselected leaves)
    log.info("Generating ROS 2 .msg files… mode=%s", mode)
    if mode.lower() == "leaf":
        msgs = generate_msgs_leaf(root, preselected=preselected)  # list[(fname, content, fields)]
    else:
        msgs = generate_msgs_leaf(root, preselected=preselected)
        msgs = generate_msgs_aggregate(root, preselected=preselected)  # list[(fname, content, fields)]

    # 4) Prepare output dirs
    pkg_dir = output / package_name
    msg_dir = pkg_dir / "msg"
    srv_dir = pkg_dir / "srv"
    msg_dir.mkdir(parents=True, exist_ok=True)
    if srv.lower() != "none":
        srv_dir.mkdir(parents=True, exist_ok=True)
    msg_rel_paths: List[str] = []
    srv_rel_paths: List[str] = []

    # 5) Write .msg files from VSS
    for fname, content, fields in msgs:
        (msg_dir / fname).write_text(content, encoding="utf-8")
        msg_rel_paths.append(f"msg/{fname}")

    # 6) Write ordinary .srv files (get/set)
    if srv.lower() != "none":
        for fname, _content, fields in msgs:
            base, get_srv_name, set_srv_name, _by_time_srv_name = srv_names_for_msg(fname)
            msg_type_name = base
            if srv.lower() in ("get", "both"):
                get_content = render_get_srv(package_name, msg_type_name, fields, srv_use_msg)
                (srv_dir / get_srv_name).write_text(get_content, encoding="utf-8")
                srv_rel_paths.append(f"srv/{get_srv_name}")
            if srv.lower() in ("set", "both"):
                set_content = render_set_srv(package_name, msg_type_name, fields, srv_use_msg)
                (srv_dir / set_srv_name).write_text(set_content, encoding="utf-8")
                srv_rel_paths.append(f"srv/{set_srv_name}")

    # 9) Done
    log.info("Done. Generated %d message(s) and %d service(s) in %s", len(msg_rel_paths), len(srv_rel_paths), pkg_dir)


if __name__ == "__main__":
    cli()
