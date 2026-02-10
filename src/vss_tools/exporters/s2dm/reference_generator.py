# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""VSS reference file generation for S2DM exporter.

This module handles generation of reference files alongside GraphQL schema output.
Creates vspec_reference/ directory containing:
- VSS lookup spec (fully processed and expanded tree)
- Units definitions (if used)
- Quantities definitions (if used)
- README.md with provenance documentation
"""

from __future__ import annotations

from pathlib import Path

from vss_tools import log
from vss_tools.tree import VSSNode

from .constants import S2DMExporterException


def generate_vspec_reference(
    tree: VSSNode,
    data_type_tree: VSSNode | None,
    output_dir: Path,
    extended_attributes: tuple[str, ...],
    vspec_file: Path,
    units_files: tuple[Path, ...],
    quantities_files: tuple[Path, ...],
    mapping_metadata: dict[str, dict] | None = None,
) -> None:
    """
    Generate VSS reference files alongside GraphQL output.

    Creates vspec_reference/ directory with VSS lookup spec and input files.
    If units/quantities not provided via CLI, checks for implicit files.

    Args:
        tree: Main VSS tree
        data_type_tree: Optional data type tree
        output_dir: Output directory
        extended_attributes: Extended attributes to include
        vspec_file: Path to vspec file (to find implicit units/quantities)
        units_files: Unit files from CLI
        quantities_files: Quantity files from CLI
        mapping_metadata: Optional metadata including plural type warnings

    Raises:
        S2DMExporterException: If reference file generation fails
    """
    try:
        import shutil

        import yaml

        from vss_tools.exporters.yaml import export_yaml

        reference_dir = output_dir / "vspec_reference"

        try:
            reference_dir.mkdir(exist_ok=True)
        except PermissionError as e:
            raise S2DMExporterException(f"Permission denied creating reference directory: {reference_dir}") from e
        except OSError as e:
            raise S2DMExporterException(f"Failed to create reference directory {reference_dir}: {e}") from e

        log.info(f"Generating VSS reference files in {reference_dir}/")

        # Generate VSS lookup spec
        vspec_file_out = reference_dir / "vspec_lookup_spec.yaml"
        try:
            tree_data = tree.as_flat_dict(with_extra_attributes=False, extended_attributes=extended_attributes)
            if data_type_tree:
                tree_data["ComplexDataTypes"] = data_type_tree.as_flat_dict(
                    with_extra_attributes=False, extended_attributes=extended_attributes
                )
            export_yaml(vspec_file_out, tree_data)
            log.info(f"  - VSS lookup spec: {vspec_file_out.name}")
        except Exception as e:
            raise S2DMExporterException(f"Failed to generate VSS lookup spec {vspec_file_out}: {e}") from e

        # Determine actual units files used (explicit or implicit)
        actual_units = units_files
        if not actual_units:
            implicit_units = vspec_file.parent / "units.yaml"
            if implicit_units.exists():
                actual_units = (implicit_units,)

        # Copy/merge units files if any were used
        if actual_units:
            units_output = reference_dir / "vspec_units.yaml"
            try:
                if len(actual_units) == 1:
                    shutil.copy2(actual_units[0], units_output)
                else:
                    merged = {}
                    for unit_file in actual_units:
                        try:
                            with open(unit_file) as inf:
                                if data := yaml.safe_load(inf):
                                    merged.update(data)
                        except yaml.YAMLError as e:
                            raise S2DMExporterException(f"Invalid YAML in units file {unit_file}: {e}") from e
                        except FileNotFoundError:
                            raise S2DMExporterException(f"Units file not found: {unit_file}") from None

                    with open(units_output, "w") as outf:
                        yaml.dump(merged, outf, default_flow_style=False, sort_keys=True)

                log.info(f"  - Units file: {units_output.name}")
            except S2DMExporterException:
                raise
            except (PermissionError, OSError) as e:
                raise S2DMExporterException(f"Failed to write units file {units_output}: {e}") from e

        # Determine actual quantities files used (explicit or implicit)
        actual_quantities = quantities_files
        if not actual_quantities:
            implicit_quantities = vspec_file.parent / "quantities.yaml"
            if implicit_quantities.exists():
                actual_quantities = (implicit_quantities,)

        # Copy/merge quantities files if any were used
        if actual_quantities:
            quantities_output = reference_dir / "vspec_quantities.yaml"
            try:
                if len(actual_quantities) == 1:
                    shutil.copy2(actual_quantities[0], quantities_output)
                else:
                    merged = {}
                    for qty_file in actual_quantities:
                        try:
                            with open(qty_file) as inf:
                                if data := yaml.safe_load(inf):
                                    merged.update(data)
                        except yaml.YAMLError as e:
                            raise S2DMExporterException(f"Invalid YAML in quantities file {qty_file}: {e}") from e
                        except FileNotFoundError:
                            raise S2DMExporterException(f"Quantities file not found: {qty_file}") from None

                    with open(quantities_output, "w") as outf:
                        yaml.dump(merged, outf, default_flow_style=False, sort_keys=True)

                log.info(f"  - Quantities file: {quantities_output.name}")
            except S2DMExporterException:
                raise
            except (PermissionError, OSError) as e:
                raise S2DMExporterException(f"Failed to write quantities file {quantities_output}: {e}") from e

        # Write plural type warnings if any were collected
        if mapping_metadata and mapping_metadata.get("plural_type_warnings"):
            warnings_output = reference_dir / "plural_type_warnings.yaml"
            try:
                with open(warnings_output, "w") as f:
                    # Write header comment
                    f.write(
                        "# WARNING: These elements in the reference model seem to have a plural name, "
                        "while GraphQL best practices suggest the use of the singular form for type names.\n"
                    )
                    f.write("# Consider replacing plural forms and whitelisting false positives.\n\n")

                    # Write each warning as FQN with nested fields
                    for warning in mapping_metadata["plural_type_warnings"]:
                        f.write(f"{warning['fqn']}:\n")
                        f.write(f"  suggested_singular: {warning['suggested_singular']}\n")
                        f.write(f"  current_name_in_graphql_model: {warning['type_name']}\n")
                        f.write("\n")

                warning_count = len(mapping_metadata["plural_type_warnings"])
                log.info(f"  - Plural warnings: {warnings_output.name} ({warning_count} warning(s))")
            except (PermissionError, OSError) as e:
                raise S2DMExporterException(f"Failed to write plural warnings file {warnings_output}: {e}") from e

        # Write short name collisions only if short names were actually used
        # (short_name_mapping will be None when --fqn-type-names is used)
        if mapping_metadata and mapping_metadata.get("short_name_mapping") is not None:
            collisions_output = reference_dir / "short_name_collisions.yaml"
            try:
                with open(collisions_output, "w") as f:
                    # Write header comment
                    f.write("# Short Name Collision Resolution Report\n")
                    f.write("#\n")
                    f.write("# This file documents how VSS branch names were converted to GraphQL type names.\n")
                    f.write("# Resolution strategy: Progressive parent qualification\n")
                    f.write("#   1. Try short name (e.g., 'Window')\n")
                    f.write("#   2. If collision: add parent (e.g., 'Door_Window', 'Windshield_Window')\n")
                    f.write("#   3. If still collision: add more ancestors (e.g., 'Cabin_Door_Window')\n")
                    f.write("#   4. Last resort: use full FQN with underscores\n\n")

                    collision_list = mapping_metadata.get("short_name_collisions", [])
                    name_mapping = mapping_metadata.get("short_name_mapping", {})
                    stats = mapping_metadata.get("short_name_stats", {})

                    # Organize FQNs by resolution strategy
                    parent_qualified_fqns = []
                    multi_qualified_fqns = []
                    full_fqn_fqns = []

                    for fqn, assigned_name in name_mapping.items():
                        fqn_parts = fqn.split(".")
                        short_name = fqn_parts[-1]

                        if assigned_name == short_name:
                            # No collision - skip (we'll only report collisions)
                            continue
                        elif assigned_name == "_".join(fqn_parts):
                            # Full FQN used
                            full_fqn_fqns.append(fqn)
                        else:
                            # Qualified name - check depth
                            assigned_parts = assigned_name.split("_")
                            if len(assigned_parts) == 2:
                                # Parent-qualified (e.g., Parent_Name)
                                parent_qualified_fqns.append(fqn)
                            else:
                                # Multi-ancestor qualified
                                multi_qualified_fqns.append(fqn)

                    # Write summary section
                    f.write("summary:\n")
                    f.write(f"  total_branches: {len(name_mapping)}\n")
                    f.write(f"  no_collisions: {stats.get('no_collision', 0)}\n")
                    f.write(f"  parent_qualified: {stats.get('parent_qualified', 0)}\n")
                    f.write(f"  multi_ancestor_qualified: {stats.get('multi_parent_qualified', 0)}\n")
                    f.write(f"  full_fqn_fallback: {stats.get('full_fqn', 0)}\n\n")

                    # Section 1: Parent-qualified names
                    if parent_qualified_fqns:
                        f.write("# Collisions resolved by adding immediate parent name (e.g., Parent_Name)\n")
                        f.write("parent_qualified:\n")
                        for fqn in sorted(parent_qualified_fqns):
                            assigned_name = name_mapping[fqn]
                            f.write(f"  - {{ fqn: {fqn}, type: {assigned_name} }}\n")
                        f.write("\n")

                    # Section 2: Multi-ancestor qualified names
                    if multi_qualified_fqns:
                        f.write(
                            "# Collisions resolved by adding multiple ancestor names (e.g., GrandParent_Parent_Name)\n"
                        )
                        f.write("multi_ancestor_qualified:\n")
                        for fqn in sorted(multi_qualified_fqns):
                            assigned_name = name_mapping[fqn]
                            f.write(f"  - {{ fqn: {fqn}, type: {assigned_name} }}\n")
                        f.write("\n")

                    # Section 3: Full FQN names (last resort)
                    if full_fqn_fqns:
                        f.write("# Even with qualification, collisions persisted - using full FQN\n")
                        f.write("full_fqn_fallback:\n")
                        for fqn in sorted(full_fqn_fqns):
                            assigned_name = name_mapping[fqn]
                            f.write(f"  - {{ fqn: {fqn}, type: {assigned_name} }}\n")
                        f.write("\n")

                    # Section 4: Collision groups (detailed view by short name)
                    if collision_list:
                        f.write("# Detailed collision groups: branches that share the same short name\n")
                        f.write("collision_groups:\n")
                        for collision in sorted(collision_list, key=lambda x: x["short_name"]):
                            short_name = collision["short_name"]
                            f.write(f"  {short_name}:  # {collision['collision_count']} branches share this name\n")
                            for fqn in sorted(collision["fqns"]):
                                assigned_name = collision["assigned_names"][fqn]
                                f.write(f"    - {{ fqn: {fqn}, type: {assigned_name} }}\n")
                        f.write("\n")

                total_count = len(name_mapping) if name_mapping else 0
                collision_count = len(collision_list) if collision_list else 0
                log.info(
                    f"  - Short name resolution: {collisions_output.name} ({total_count} branches, "
                    + f"{collision_count} collision groups)"
                )
            except (PermissionError, OSError) as e:
                raise S2DMExporterException(
                    f"Failed to write short name collisions file {collisions_output}: {e}"
                ) from e

        # Write pluralized field names if any were collected
        if mapping_metadata and mapping_metadata.get("pluralized_field_names"):
            pluralized_output = reference_dir / "pluralized_field_names.yaml"
            try:
                with open(pluralized_output, "w") as f:
                    # Write header comment
                    f.write(
                        "# Following names were changed to their plural form as they resolve to an output type "
                        "with a List type modifier.\n\n"
                    )

                    # Write each pluralized field as FQN with nested fields
                    for entry in mapping_metadata["pluralized_field_names"]:
                        f.write(f"{entry['fqn']}:\n")
                        f.write(f"  plural_field_name: {entry['plural_field_name']}\n")
                        f.write(f"  path_in_graphql_model: {entry['path_in_graphql_model']}\n")
                        f.write("\n")

                log.info(
                    f"  - Pluralized fields: {pluralized_output.name} "
                    f"({len(mapping_metadata['pluralized_field_names'])} field(s))"
                )
            except (PermissionError, OSError) as e:
                raise S2DMExporterException(f"Failed to write pluralized fields file {pluralized_output}: {e}") from e

        # Generate README.md for provenance documentation
        has_plural_warnings = bool(mapping_metadata and mapping_metadata.get("plural_type_warnings"))
        generate_reference_readme(reference_dir, vspec_file, actual_units, actual_quantities, has_plural_warnings)

    except S2DMExporterException:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors and wrap them
        raise S2DMExporterException(f"Unexpected error generating VSS reference files: {e}") from e


def generate_reference_readme(
    reference_dir: Path,
    vspec_file: Path,
    units_files: tuple[Path, ...] | None,
    quantities_files: tuple[Path, ...] | None,
    has_plural_warnings: bool = False,
) -> None:
    """
    Generate README.md documenting the provenance of reference files.

    Args:
        reference_dir: Directory where reference files are stored
        vspec_file: Original vspec input file
        units_files: Units files used (explicit or implicit)
        quantities_files: Quantities files used (explicit or implicit)
        has_plural_warnings: Whether plural type warnings were generated

    Raises:
        S2DMExporterException: If README generation fails
    """
    try:
        from importlib.metadata import version

        try:
            vss_tools_version = version("vss-tools")
        except Exception:
            vss_tools_version = "unknown"
            log.warning("Could not determine vss-tools version")

        readme_content = f"""# VSS Reference Files

This directory contains the exact information used to generate the S2DM GraphQL schema.

- Version used: [vss-tools](https://github.com/COVESA/vss-tools) `{vss_tools_version}`.
- Execute `vspec export s2dm --help` in the tools for more details.

It could serve as a supporting reference for traceability or debugging.

## Files

* **vspec_lookup_spec.yaml** - Complete VSS specification tree (fully processed and expanded)."""

        if units_files:
            readme_content += """
* **vspec_units.yaml** - Unit definitions for VSS signals."""

        if quantities_files:
            readme_content += """
* **vspec_quantities.yaml** - Quantity definitions categorizing measurements."""

        if has_plural_warnings:
            readme_content += """
* **plural_type_warnings.txt** - VSS branches with plural type names (GraphQL prefers singular)."""

        readme_content += """

## Documentation

- [S2DM Exporter](https://github.com/COVESA/vss-tools/blob/master/docs/s2dm.md)
- [VSS Tools](https://github.com/COVESA/vss-tools)
- [COVESA VSS](https://github.com/COVESA/vehicle_signal_specification)
- [COVESA S2DM](https://covesa.github.io/s2dm)
"""

        readme_path = reference_dir / "README.md"

        try:
            with open(readme_path, "w") as f:
                f.write(readme_content)
            log.info(f"  - README: {readme_path.name}")
        except (PermissionError, OSError) as e:
            raise S2DMExporterException(f"Failed to write README file {readme_path}: {e}") from e

    except S2DMExporterException:
        raise
    except Exception as e:
        raise S2DMExporterException(f"Unexpected error generating README: {e}") from e
