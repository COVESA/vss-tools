# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
GraphQL directive processing using string templates.

This module provides a hybrid approach that uses GraphQL-core for schema
validation and string templates for directive injection. It replaces the
brittle string manipulation approach with a more maintainable template system.
"""

from string import Template

from graphql import GraphQLSchema, print_schema

from vss_tools.utils.graphql_utils import GraphQLElementType, convert_name_for_graphql_schema


class GraphQLDirectiveProcessor:
    """Processes GraphQL schema SDL to inject VSS-specific directives using templates."""

    # Template definitions for directive types
    TEMPLATES = {
        "range": Template("@range($args)"),
        "deprecated": Template('@deprecated(reason: "$reason")'),
    }

    def process_schema(
        self, schema: GraphQLSchema, unit_enums_metadata: dict, allowed_enums_metadata: dict, vspec_comments: dict
    ) -> str:
        """
        Process schema SDL to inject directives using templates.

        Args:
            schema: GraphQL schema from graphql-core
            unit_enums_metadata: Unit enum metadata
            allowed_enums_metadata: Allowed enum metadata
            vspec_comments: VSS comment and directive data

        Returns:
            SDL string with injected directives
        """
        # Start with standard GraphQL-core SDL output
        sdl = print_schema(schema)
        lines = sdl.split("\n")

        # Process directives using templates
        processed_enum_values: set[str] = set()

        lines = self._process_unit_enum_directives(lines, unit_enums_metadata, processed_enum_values)
        lines = self._process_allowed_enum_directives(lines, allowed_enums_metadata, processed_enum_values)
        lines = self._process_field_directives(lines, vspec_comments)
        lines = self._process_deprecated_directives(lines, vspec_comments.get("field_deprecated", {}))
        lines = self._process_range_directives(lines, vspec_comments.get("field_ranges", {}))
        lines = self._process_type_directives(lines, vspec_comments)

        return "\n".join(lines)

    def _process_unit_enum_directives(
        self, lines: list[str], unit_enums_metadata: dict, processed_values: set
    ) -> list[str]:
        """
        Process unit enum directives.

        Annotates enum type with @vspec(element: QUANTITY_KIND, metadata: [{key: "quantity", value: "..."}])
        and individual enum values with @vspec(element: UNIT, metadata: [{key: "unit", value: "..."}])
        """
        for quantity, units_data in unit_enums_metadata.items():
            enum_name = f"{convert_name_for_graphql_schema(quantity, GraphQLElementType.TYPE)}UnitEnum"

            in_target_enum = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"enum {enum_name}"):
                    if "@vspec" not in line:
                        # Annotate enum type with QUANTITY_KIND
                        directive = (
                            f"@vspec(element: QUANTITY_KIND, " f'metadata: [{{key: "quantity", value: "{quantity}"}}])'
                        )
                        lines[i] = line.replace(" {", f" {directive} {{")
                    in_target_enum = True
                    continue
                elif line.strip().startswith("enum ") and in_target_enum:
                    in_target_enum = False
                    continue
                elif line.strip() == "}" and in_target_enum:
                    in_target_enum = False
                    continue

                if in_target_enum and line.strip() and not line.strip().startswith('"'):
                    stripped_line = line.strip()

                    for unit_key, unit_info in units_data.items():
                        unit_name = unit_info["name"]
                        enum_value_name = convert_name_for_graphql_schema(unit_name, GraphQLElementType.ENUM_VALUE)

                        enum_value_key = f"{enum_name}.{enum_value_name}"
                        if stripped_line.startswith(enum_value_name) and enum_value_key not in processed_values:
                            if "@vspec" not in line:
                                indent = line[: len(line) - len(line.lstrip())]
                                # Annotate enum value with UNIT
                                directive = f'@vspec(element: UNIT, metadata: [{{key: "unit", value: "{unit_key}"}}])'
                                lines[i] = f"{indent}{enum_value_name} {directive}"

                            processed_values.add(enum_value_key)
                            break
        return lines

    def _process_allowed_enum_directives(
        self, lines: list[str], allowed_enums_metadata: dict, processed_values: set
    ) -> list[str]:
        """
        Process allowed value enum directives.

        Annotates the enum type itself with @vspec(element, fqn, metadata),
        but does NOT annotate individual enum values.
        """
        for enum_name, enum_data in allowed_enums_metadata.items():
            fqn = enum_data.get("fqn", "")
            vss_type = enum_data.get("vss_type", "ATTRIBUTE")
            allowed_values_dict = enum_data.get("allowed_values", {})

            # Build the allowed values list for metadata
            allowed_values_list = list(allowed_values_dict.values())
            allowed_str = ", ".join([f'"{v}"' for v in allowed_values_list])

            for i, line in enumerate(lines):
                if line.strip().startswith(f"enum {enum_name}") and "@vspec" not in line:
                    # Annotate the enum type (not individual values)
                    # Format: @vspec(element: ATTRIBUTE, fqn: "...", metadata: [{key: "allowed", value: "[...]"}])
                    directive = (
                        f'@vspec(element: {vss_type}, fqn: "{fqn}", '
                        f'metadata: [{{key: "allowed", value: "[{allowed_str}]"}}])'
                    )
                    lines[i] = line.replace(" {", f" {directive} {{")
                    break

        return lines

    def _process_field_directives(self, lines: list[str], vspec_comments: dict) -> list[str]:
        """Process consolidated field @vspec directives (element + fqn + optional metadata)."""
        # Process VSS type information (element + fqn + metadata)
        for field_path, vss_info in vspec_comments.get("field_vss_types", {}).items():
            type_name, field_name = field_path.split(".", 1)  # Use maxsplit=1 to handle field names with dots
            element = vss_info["element"]
            fqn = vss_info["fqn"]
            instantiate = vss_info.get("instantiate")  # Check if this is a hoisted non-instantiated field

            in_type = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"type {type_name}"):
                    in_type = True
                    continue
                elif line.strip().startswith("type ") and in_type:
                    in_type = False
                    continue
                elif line.strip() == "}" and in_type:
                    in_type = False
                    continue

                if in_type and line.strip().startswith(f"{field_name}") and "@vspec" not in line:
                    # Build directive with element (mandatory), fqn, and optional metadata
                    if instantiate is False:
                        # Add metadata for hoisted non-instantiated fields
                        directive = (
                            f'@vspec(element: {element}, fqn: "{fqn}", '
                            f'metadata: [{{key: "instantiate", value: "false"}}])'
                        )
                    else:
                        # Standard directive without metadata
                        directive = f'@vspec(element: {element}, fqn: "{fqn}")'

                    lines[i] = line.rstrip() + f" {directive}"
                    break

        return lines

    def _process_deprecated_directives(self, lines: list[str], field_deprecated: dict) -> list[str]:
        """Process @deprecated directives using templates."""
        for field_path, reason in field_deprecated.items():
            escaped_reason = reason.replace('"', '\\"')
            type_name, field_name = field_path.split(".")

            in_type = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"type {type_name}"):
                    in_type = True
                    continue
                elif line.strip().startswith("type ") and in_type:
                    in_type = False
                    continue
                elif line.strip() == "}" and in_type:
                    in_type = False
                    continue

                if (
                    in_type
                    and field_name in line
                    and ":" in line
                    and not line.strip().startswith('"')
                    and "@deprecated" not in line
                ):
                    insert_line = i + 1
                    while insert_line < len(lines) and lines[insert_line].strip().startswith("@vspec"):
                        insert_line += 1

                    if insert_line < len(lines) and "@deprecated" not in lines[insert_line]:
                        directive = self.TEMPLATES["deprecated"].substitute(reason=escaped_reason)
                        lines.insert(insert_line, f"    {directive}")
                    break
        return lines

    def _process_range_directives(self, lines: list[str], field_ranges: dict) -> list[str]:
        """Process @range directives using templates."""
        for field_path, range_data in field_ranges.items():
            range_args = []
            min_val = range_data.get("min")
            max_val = range_data.get("max")

            # Handle both None and empty string cases
            if min_val is not None and min_val != "":
                range_args.append(f"min: {min_val}")
            if max_val is not None and max_val != "":
                range_args.append(f"max: {max_val}")

            if not range_args:
                continue

            type_name, field_name = field_path.split(".")

            in_type = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"type {type_name}"):
                    in_type = True
                    continue
                elif line.strip().startswith("type ") and in_type:
                    in_type = False
                    continue
                elif line.strip() == "}" and in_type:
                    in_type = False
                    continue

                if (
                    in_type
                    and field_name in line
                    and ":" in line
                    and not line.strip().startswith('"')
                    and "@range" not in line
                ):
                    insert_line = i + 1
                    while insert_line < len(lines) and (
                        lines[insert_line].strip().startswith("@vspec")
                        or lines[insert_line].strip().startswith("@deprecated")
                    ):
                        insert_line += 1

                    if insert_line < len(lines) and "@range" not in lines[insert_line]:
                        directive = self.TEMPLATES["range"].substitute(args=", ".join(range_args))
                        lines.insert(insert_line, f"    {directive}")
                    break
        return lines

    def _process_type_directives(self, lines: list[str], vspec_comments: dict) -> list[str]:
        """Process type-level directives (element + fqn + optional metadata for instance tags)."""
        for i, line in enumerate(lines):
            if line.strip().startswith("type "):
                type_line = line.strip()

                type_part = type_line[5:]  # Remove "type "
                if " {" in type_part:
                    type_name = type_part.split(" {")[0].strip()
                elif " @" in type_part:
                    type_name = type_part.split(" @")[0].strip()
                else:
                    continue

                instance_tag_info = vspec_comments.get("instance_tags", {}).get(type_name)
                needs_instance_tag = instance_tag_info is not None
                needs_vss_type = type_name in vspec_comments.get("vss_types", {})

                if needs_instance_tag or needs_vss_type:
                    new_line = f"type {type_name}"

                    # Add @instanceTag directive first if needed
                    if needs_instance_tag and "@instanceTag" not in line:
                        new_line += " @instanceTag"

                    # Add @vspec directive
                    if needs_instance_tag and "@vspec" not in line:
                        # Instance tag types get special metadata with instances
                        element = instance_tag_info["element"]
                        fqn = instance_tag_info["fqn"]
                        instances = instance_tag_info["instances"]
                        directive = (
                            f'@vspec(element: {element}, fqn: "{fqn}", '
                            f'metadata: [{{key: "instances", value: "{instances}"}}])'
                        )
                        new_line += f" {directive}"
                    elif needs_vss_type and "@vspec" not in line:
                        # Regular types get element + fqn only
                        vss_info = vspec_comments["vss_types"][type_name]
                        element = vss_info["element"]
                        fqn = vss_info["fqn"]
                        directive = f'@vspec(element: {element}, fqn: "{fqn}")'
                        new_line += f" {directive}"

                    new_line += " {"
                    lines[i] = new_line  # No extra indentation

        return lines
