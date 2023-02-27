import pytest
import os

from vspec.model.constants import VSSType, VSSDataType, Unit, StringStyle, VSSTreeType, VSSConstant


@pytest.mark.parametrize("style_enum, style_str",
                         [(StringStyle.NONE, "none"),
                             (StringStyle.CAMEL_CASE, "camelCase"),
                             (StringStyle.CAMEL_BACK, "camelBack"),
                             (StringStyle.CAPITAL_CASE, "capitalcase"),
                             (StringStyle.CONST_CASE, "constcase"),
                             (StringStyle.LOWER_CASE, "lowercase"),
                             (StringStyle.PASCAL_CASE, "pascalcase"),
                             (StringStyle.SENTENCE_CASE, "sentencecase"),
                             (StringStyle.SNAKE_CASE, "snakecase"),
                             (StringStyle.TITLE_CASE, "titlecase"),
                             (StringStyle.TRIM_CASE, "trimcase"),
                             (StringStyle.UPPER_CASE, "uppercase"),
                             (StringStyle.ALPHANUM_CASE, "alphanumcase")])
def test_string_styles(style_enum, style_str):
    """
    Test correct parsing of string styles
    """
    assert style_enum == StringStyle.from_str(style_str)


def test_invalid_string_styles():
    with pytest.raises(Exception):
        StringStyle.from_str("not_a_valid_case")


def test_manually_loaded_units():
    """
    Test correct parsing of units
    """
    unit_file = os.path.join(os.path.dirname(__file__), 'explicit_units.yaml')
    Unit.load_config_file(unit_file)
    assert Unit.PUNCHEON == Unit.from_str("puncheon")
    assert Unit.HOGSHEAD == Unit.from_str("hogshead")


def test_invalid_unit():
    with pytest.raises(Exception):
        Unit.from_str("not_a_valid_case")


@pytest.mark.parametrize("type_enum,type_str",
                         [(VSSType.BRANCH, "branch"),
                          (VSSType.ATTRIBUTE, "attribute"),
                          (VSSType.SENSOR, "sensor"),
                          (VSSType.ACTUATOR, "actuator"),
                          (VSSType.PROPERTY, "property")])
def test_vss_types(type_enum, type_str, ):
    """
    Test correct parsing of VSS Types
    """

    assert type_enum == VSSType.from_str(type_str)


def test_invalid_vss_types():
    with pytest.raises(Exception):
        VSSType.from_str("not_a_valid_case")


@pytest.mark.parametrize("data_type_enum,data_type_str",
                         [(VSSDataType.INT8, "int8"),
                          (VSSDataType.UINT8, "uint8"),
                          (VSSDataType.INT16, "int16"),
                          (VSSDataType.UINT16, "uint16"),
                          (VSSDataType.INT32, "int32"),
                          (VSSDataType.UINT32, "uint32"),
                          (VSSDataType.INT64, "int64"),
                          (VSSDataType.UINT64, "uint64"),
                          (VSSDataType.BOOLEAN, "boolean"),
                          (VSSDataType.FLOAT, "float"),
                          (VSSDataType.DOUBLE, "double"),
                          (VSSDataType.STRING, "string")])
def test_vss_data_types(data_type_enum, data_type_str, ):
    """
    Test correct parsing of VSS Data Types
    """
    assert data_type_enum == VSSDataType.from_str(data_type_str)


def test_invalid_vss_data_types():
    with pytest.raises(Exception):
        VSSDataType.from_str("not_a_valid_case")


@pytest.mark.parametrize("tree_type_enum,tree_type_str, important_types",
                         [(VSSTreeType.SIGNAL_TREE, "signal_tree", ["sensor", "actuator", "attribute", "branch"]),
                          (VSSTreeType.DATA_TYPE_TREE, "data_type_tree", ["struct", "property", "branch"])])
def test_vss_tree_types(tree_type_enum, tree_type_str, important_types):
    """
    Test correct parsing of VSS Tree Types
    """

    assert tree_type_enum == VSSTreeType.from_str(tree_type_str)
    available_types = tree_type_enum.available_types()
    for t in important_types:
        assert t in available_types


def test_invalid_vss_tree_types():
    with pytest.raises(Exception):
        VSSDataType.from_str("not_a_valid_case")


def test_vss_constants():
    """ Test VSSConstant class """
    item = VSSConstant("mylabel", "myvalue", "mydescription", "mydomain")
    assert item.value == "myvalue"
    assert item.label == "mylabel"
    assert item.description == "mydescription"
    assert item.domain == "mydomain"
    # String subclass so just comparing shall get "value"
    assert item == "myvalue"
