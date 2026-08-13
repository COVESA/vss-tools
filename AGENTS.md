# AGENTS.md

Context for AI coding agents (and humans) working in this repository.

This is a fork of [COVESA/vss-tools](https://github.com/COVESA/vss-tools)
maintained by Ulf Björkengren (`ulfbj/vss-tools`). It is used locally / not
currently intended to be upstreamed as a PR to COVESA.

## `him-support` branch: HIM profile support

The `him-support` branch adds support for the three profiles defined by the
[COVESA Hierarchical Information Model (HIM)](https://github.com/COVESA/hierarchical_information_model),
in addition to the historic VSS rule set that vss-tools originally only supported.

### Background / motivation

VSS-tools parses `vspec` files where every node has a `type` key (e.g.
`branch`, `sensor`, `attribute`, ...). The set of valid `type` values and how
nodes may be nested was historically hardcoded to match the VSS rule set only.
The HIM project (also maintained by Ulf Björkengren) generalizes this into
three profiles with different node type sets:

- **`vehicle-data`** (default, unchanged historic behavior): `branch`,
  `sensor`, `actuator`, `attribute`, `struct`, `property`.
- **`data`** (HIM Data Rule Set): `branch`, `ro`, `rw`, `struct`, `property`.
- **`service`** (HIM Service Rule Set): `branch`, `procedure`, `iostruct`,
  `symlink`, `attribute`, `struct`, `property`.

`struct`/`property`/`branch` are common across all profiles (needed to build
a `Types` tree via `--types` regardless of the active profile for the main
tree). `attribute` is also usable in the `service` profile only as the
mandatory `Version` child of a `procedure` node.

### How to use it

```bash
vspec --profile vehicle-data export json ...   # default, unchanged behavior
vspec --profile data export json ...           # ro/rw node types
vspec --profile service export json ...        # procedure/iostruct/symlink node types
```

`--profile` is a **top-level** option (like `--log-level`), not per-exporter,
so every exporter (json/yaml/protobuf/csv/...) automatically respects it with
no per-exporter code changes needed.

### Implementation pointers

- `src/vss_tools/model.py`:
  - `Profile` enum (`vehicle-data`/`data`/`service`) and
    `PROFILE_ALLOWED_TYPES` mapping.
  - `active_profile` module-level global, set once by `cli.py` at startup.
    Mirrors the existing `dynamic_units`/`dynamic_quantities` global-state
    pattern already used for units/quantities configuration.
  - A pydantic field validator on `VSSData.type` rejects `type` values not in
    `PROFILE_ALLOWED_TYPES[active_profile]`.
  - New node data classes: `VSSDataRo`, `VSSDataRw` (data profile),
    `VSSDataProcedure`, `VSSDataIostruct`, `VSSDataSymlink` (service
    profile), wired into `TYPE_CLASS_MAP`.
  - Also fixed a pre-existing bug where `TYPE_CLASS_MAP[NodeType.ACTUATOR]`
    incorrectly pointed at `VSSDataSensor` instead of `VSSDataActuator`
    (harmless before since both classes were identical, but relevant now
    that per-type validators exist).
- `src/vss_tools/main.py`: `get_invalid_node_msgs()` extended with the
  additional parent/child structural rules for the new node types (e.g.
  `iostruct` needs a `procedure`/`branch` parent, `symlink` needs an
  `iostruct` parent, `property` also accepts an `iostruct` parent,
  `attribute` also accepts a `procedure` parent for the `Version` node).
- `src/vss_tools/cli.py` / `cli_options.py`: new global `--profile` option
  on the root `vspec` command.
- `tests/vspec/test_profiles/`: end-to-end CLI tests (subprocess-based,
  matching existing test conventions) for all three profiles, cross-profile
  rejection, and service-profile structural rules.
- `docs/vspec_arch.md` (`## HIM Profiles` section) and `README.md`: user
  facing documentation.

### Deliberate scope limitations (discussed and agreed with the maintainer)

These were explicitly out of scope for the initial implementation ("core
structure only" for the service profile):

- No enforcement that a `procedure` node actually has a `Version` child
  (only that *if* an `attribute` node is a child of a `procedure`, that
  nesting is structurally allowed).
- No validation of `procedure`'s optional `nativeRate`/`timeToLive` beyond
  non-negative-integer checks (no cross-field consistency rules).
- No cross-tree resolution of `symlink` targets (`path`/`domain`/`version`
  pointing at a leaf node in a *different* HIM tree) — vss-tools operates on
  a single tree at a time, so this would require loading and cross-referencing
  multiple domain trees, which is a larger architectural change.

If asked to extend HIM support, check with the user whether these should now
be implemented, since they were previously deferred by choice, not oversight.

### Verification approach used

Since this environment initially had no git/Python/uv installed, they were
installed via `winget` (`Git.Git`, `Python.Python.3.12`) and `pip install uv`
before running `uv sync` and the test suite. Before/after full test suite
runs (`pytest tests --ignore=tests/backward_compatibility`) were diffed to
confirm zero regressions — there are ~74 pre-existing environment-only
failures on Windows (`AssertionError`/`filecmp` mismatches, likely CRLF line
ending differences from a Windows git checkout) unrelated to any changes
here; the exact same 74 tests fail before and after this feature.

### Notes on installing/testing this branch elsewhere

Since this is not published to PyPI, install with:

```bash
pip install git+https://github.com/ulfbj/vss-tools.git@him-support
```

or for local iterative development from a clone:

```bash
git clone https://github.com/ulfbj/vss-tools.git
cd vss-tools && git checkout him-support
pip install -e .
```

Do **not** confuse this with `pip install git+https://github.com/COVESA/vss-tools.git`
(the upstream repo) — that will not have `--profile` since the feature only
exists on this fork's `him-support` branch.
