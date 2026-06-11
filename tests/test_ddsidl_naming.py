# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from vss_tools.exporters.ddsidl import getAllowedName


class TestDdsIdlNaming:
    """Tests for getAllowedName, which prefixes reserved-word identifiers."""

    def test_passes_through_normal_names(self):
        """Names that aren't reserved should be returned unchanged."""
        assert getAllowedName("speed") == "speed"
        assert getAllowedName("Vehicle") == "Vehicle"
        assert getAllowedName("Foo123") == "Foo123"

    def test_prefixes_python_keywords(self):
        """Python reserved words should get a leading underscore.

        Regression test: previously the keyword.iskeyword() call was missing
        its parentheses on its argument (`name.lower` instead of
        `name.lower()`), so a bound-method object was passed to iskeyword
        instead of the lowered string. iskeyword returned False, so VSS
        signals named with Python keywords that aren't also C/IDL keywords
        (e.g. 'class', 'def', 'import', 'lambda') passed through silently
        and ended up as raw identifiers in the generated IDL.
        """
        assert getAllowedName("class") == "_class"
        assert getAllowedName("def") == "_def"
        assert getAllowedName("import") == "_import"
        assert getAllowedName("lambda") == "_lambda"
        # Case-insensitive: same effect for differently-cased input.
        assert getAllowedName("Class") == "_Class"
        assert getAllowedName("CLASS") == "_CLASS"

    def test_prefixes_idl_keywords(self):
        """IDL reserved words should get a leading underscore."""
        assert getAllowedName("interface") == "_interface"
        assert getAllowedName("module") == "_module"
        assert getAllowedName("attribute") == "_attribute"

    def test_prefixes_c_keywords(self):
        """C reserved words should get a leading underscore.

        Some of these (`if`, `for`, `while`, `return`) are also Python
        keywords, but C-keyword detection caught them already even with
        the iskeyword bug.
        """
        assert getAllowedName("auto") == "_auto"
        assert getAllowedName("typedef") == "_typedef"
        assert getAllowedName("sizeof") == "_sizeof"
