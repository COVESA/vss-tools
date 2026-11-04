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

import re
from string import Template

from graphql import GraphQLSchema, print_schema

from .predefined_elements import qudt_vocab


class GraphQLDirectiveProcessor:
    """Processes GraphQL schema SDL to inject VSS-specific directives for S2DM export using templates."""

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
        lines = self._process_instance_dimension_enum_directives(
            lines, vspec_comments.get("instance_dimension_enums", {}), processed_enum_values
        )
        lines = self._process_field_directives(lines, vspec_comments)
        lines = self._process_instance_tag_field_directives(lines, vspec_comments)
        lines = self._process_deprecated_directives(lines, vspec_comments.get("field_deprecated", {}))
        lines = self._process_range_directives(lines, vspec_comments.get("field_ranges", {}))
        lines = self._process_type_directives(lines, vspec_comments)

        return "\n".join(lines)

    def _process_unit_enum_directives(
        self, lines: list[str], unit_enums_metadata: dict, processed_values: set
    ) -> list[str]:
        """
        Process unit enum directives.

        The enum type gets @vspec(element: QUANTITY_KIND, originalName: "{vss_quantity}") and, for QUDT enums,
        the QUDT quantity-kind @reference. Every value of a QUDT enum keeps its QUDT @reference, and values
        that are VSS units additionally get @vspec(element: UNIT, originalName: "{vss_key}").
        """
        for quantity_data in unit_enums_metadata.values():
            enum_name = quantity_data["enum_name"]
            vss_quantity = quantity_data.get("vss_quantity", "")
            qudt_backed = quantity_data.get("qudt_backed", False)
            quantity_kind_uri = qudt_vocab.get_quantity_kind_uri(enum_name) if qudt_backed else None
            unit_uris = qudt_vocab.get_unit_uris(enum_name) if qudt_backed else {}

            vss_key_by_value: dict[str, str] = {}
            for vss_key, unit_info in quantity_data.get("units", {}).items():
                vss_key_by_value.setdefault(unit_info["qudt_unit"], vss_key)

            start = next((i for i, line in enumerate(lines) if re.match(rf"enum {enum_name}\b", line.strip())), None)
            if start is None:
                continue

            if "@vspec" not in lines[start]:
                type_directives = []
                if vss_quantity:
                    type_directives.append(f'@vspec(element: QUANTITY_KIND, originalName: "{vss_quantity}")')
                if quantity_kind_uri:
                    type_directives.append(f'@reference(uri: "{quantity_kind_uri}")')
                if type_directives:
                    lines[start] = re.sub(r"\s*\{\s*$", f" {' '.join(type_directives)} {{", lines[start])

            in_description = False
            for i in range(start + 1, len(lines)):
                stripped = lines[i].strip()
                if stripped == "}":
                    break
                if in_description:
                    in_description = not stripped.endswith('"""')
                    continue
                if stripped.startswith('"""'):
                    in_description = not (len(stripped) > 3 and stripped.endswith('"""'))
                    continue

                match = re.match(r"(\s*)([_A-Za-z][_0-9A-Za-z]*)(.*)$", lines[i])
                if not match or "@vspec" in lines[i]:
                    continue
                indent, value_name, rest = match.groups()
                value_directives = []
                if value_name in vss_key_by_value:
                    value_directives.append(f'@vspec(element: UNIT, originalName: "{vss_key_by_value[value_name]}")')
                if value_name in unit_uris:
                    value_directives.append(f'@reference(uri: "{unit_uris[value_name]}")')
                if value_directives:
                    lines[i] = f"{indent}{value_name} {' '.join(value_directives)}{rest}"
                processed_values.add(f"{enum_name}.{value_name}")
        return lines

    def _process_allowed_enum_directives(
        self, lines: list[str], allowed_enums_metadata: dict, processed_values: set
    ) -> list[str]:
        """
        Process allowed value enum directives.

        Annotates the enum type itself with @vspec(element, fqn).
        Annotates individual enum values that were sanitized with @vspec(metadata: originalName).
        """
        for enum_name, enum_data in allowed_enums_metadata.items():
            fqn = enum_data.get("fqn", "")
            vss_type = enum_data.get("vss_type", "ATTRIBUTE")
            modified_values = enum_data.get("modified_values", {})

            in_target_enum = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"enum {enum_name}"):
                    if "@vspec" not in line:
                        directive = f'@vspec(element: {vss_type}, fqn: "{fqn}")'
                        lines[i] = line.replace(" {", f" {directive} {{")
                    in_target_enum = True
                    continue
                elif line.strip().startswith("enum ") and in_target_enum:
                    in_target_enum = False
                    continue
                elif line.strip() == "}" and in_target_enum:
                    in_target_enum = False
                    continue

                # Process individual enum values that were modified
                if in_target_enum and line.strip() and not line.strip().startswith('"'):
                    stripped_line = line.strip()

                    for enum_value_name, original_value in modified_values.items():
                        enum_value_key = f"{enum_name}.{enum_value_name}"
                        if stripped_line.startswith(enum_value_name) and enum_value_key not in processed_values:
                            if "@vspec" not in line:
                                indent = line[: len(line) - len(line.lstrip())]
                                directive = f'@vspec(originalName: "{original_value}")'
                                lines[i] = f"{indent}{enum_value_name} {directive}"

                            processed_values.add(enum_value_key)
                            break

        return lines

    def _process_instance_dimension_enum_directives(
        self, lines: list[str], instance_dimension_enums: dict, processed_values: set
    ) -> list[str]:
        """
        Process instance dimension enum directives.

        Annotates enum values that were modified during sanitization with their original names.
        """
        for enum_name, enum_data in instance_dimension_enums.items():
            modified_values = enum_data.get("modified_values", {})
            if not modified_values:
                continue

            in_target_enum = False

            for i, line in enumerate(lines):
                # Detect enum start
                if line.strip().startswith(f"enum {enum_name}"):
                    in_target_enum = True
                    continue
                elif line.strip().startswith("enum ") and in_target_enum:
                    in_target_enum = False
                    continue
                elif line.strip() == "}" and in_target_enum:
                    in_target_enum = False
                    continue

                # Process enum values within target enum
                if in_target_enum and line.strip() and not line.strip().startswith('"'):
                    stripped_line = line.strip()

                    for enum_value_name, original_value in modified_values.items():
                        enum_value_key = f"{enum_name}.{enum_value_name}"

                        if stripped_line.startswith(enum_value_name) and enum_value_key not in processed_values:
                            if "@vspec" not in line:
                                indent = line[: len(line) - len(line.lstrip())]
                                directive = f'@vspec(originalName: "{original_value}")'
                                lines[i] = f"{indent}{enum_value_name} {directive}"

                            processed_values.add(enum_value_key)
                            break

        return lines

    def _process_field_directives(self, lines: list[str], vspec_comments: dict) -> list[str]:
        """Process field @vspec directives (element + fqn)."""
        for field_path, vss_info in vspec_comments.get("field_vss_types", {}).items():
            type_name, field_name = field_path.split(".", 1)  # Use maxsplit=1 to handle field names with dots
            element = vss_info["element"]
            fqn = vss_info["fqn"]

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
                    lines[i] = line.rstrip() + f' @vspec(element: {element}, fqn: "{fqn}")'
                    break

        return lines

    def _process_instance_tag_field_directives(self, lines: list[str], vspec_comments: dict) -> list[str]:
        """Annotate the `instanceTag` field of types that have instances with @instanceTag."""
        type_names = set(vspec_comments.get("instance_tag_types", {}))
        in_target_type = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("type "):
                in_target_type = stripped[5:].split(" ")[0] in type_names
            elif stripped == "}":
                in_target_type = False
            elif in_target_type and stripped.startswith("instanceTag:") and "@instanceTag" not in line:
                lines[i] = line.rstrip() + " @instanceTag"
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
                        element = instance_tag_info["element"]
                        fqn = instance_tag_info["fqn"]
                        new_line += f' @vspec(element: {element}, fqn: "{fqn}")'
                    elif needs_vss_type and "@vspec" not in line:
                        vss_info = vspec_comments["vss_types"][type_name]
                        element = vss_info["element"]
                        fqn = vss_info["fqn"]
                        new_line += f' @vspec(element: {element}, fqn: "{fqn}")'

                    new_line += " {"
                    lines[i] = new_line  # No extra indentation

        return lines
