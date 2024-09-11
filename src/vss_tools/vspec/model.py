# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import re
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from rich.pretty import pretty_repr
from typing_extensions import Self

from vss_tools import log
from vss_tools.vspec.datatypes import (
    Datatypes,
    dynamic_quantities,
    dynamic_units,
    get_all_datatypes,
    is_array,
    resolve_datatype,
)

EXPORT_EXCLUDE_ATTRIBUTES = ["delete", "instantiate", "fqn", "arraysize", "aggregate", "is_instance"]


class ModelException(Exception):
    pass


class ModelValidationException(Exception):
    """
    Exception that pretty formats the Pydantic
    ValidationError
    """

    def __init__(self, element: str | None, ve: ValidationError):
        self.element = element
        self.ve = ve

    def __str__(self) -> str:
        errors = self.ve.errors(include_url=False)
        return f"'{self.element}' has {len(errors)} model error(s):\n{pretty_repr(errors)}"


class NodeType(str, Enum):
    BRANCH = "branch"
    ATTRIBUTE = "attribute"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    STRUCT = "struct"
    PROPERTY = "property"


class VSSRaw(BaseModel):
    """
    Most low level model that accepts everything
    In the end we need that to support the scenario
    of being able to overlay things that have been
    unrolled through instances.
    Not only that but to support defining those elements
    incomplete in terms of our model.
    After expanding instances we convert all raw nodes
    """

    fqn: str | None = None

    model_config = ConfigDict(extra="allow")

    def get_extra_attributes(self) -> list[str]:
        defined_fields = self.model_fields.keys()
        additional_fields = set(self.model_dump().keys()) - set(defined_fields)
        return list(additional_fields)

    def as_dict(
        self,
        with_extra_attributes: bool = True,
        exclude_fields: list[str] = EXPORT_EXCLUDE_ATTRIBUTES,
        extended_attributes: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        excludes = exclude_fields.copy()
        if not with_extra_attributes:
            for extra_attribute in self.get_extra_attributes():
                if extra_attribute not in extended_attributes:
                    excludes.append(extra_attribute)
        data = {}
        for k, v in self.model_dump(mode="json", exclude_none=False, exclude=set(excludes)).items():
            if k not in extended_attributes:
                if v == []:
                    continue
                if v is None:
                    continue
            data[k] = v
        return data


class VSSData(VSSRaw):
    model_config = ConfigDict(extra="allow")
    type: NodeType
    description: str
    comment: str | None = None
    delete: bool = False
    deprecation: str | None = None
    constUID: str | None = None
    fka: list[str] = []
    instantiate: bool = True

    @field_validator("constUID")
    @classmethod
    def check_const_uid_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        pattern = r"^0x[0-9A-Fa-f]{8}$"
        assert bool(re.match(pattern, v)), f"'{v}' is not a valid 'constUID'"
        return v


class VSSDataBranch(VSSData):
    instances: Any = None
    aggregate: bool = False
    is_instance: bool = False

    @field_validator("instances")
    @classmethod
    def fill_instances(cls, v: Any) -> list[str]:
        """
        Instances can be specified as a string or a list
        and even of a list of lists.
        Normalizing it to be a list
        """
        if v is None:
            return []
        if not (isinstance(v, str) or isinstance(v, list)):
            assert False, f"'{v}' is not a valid 'instances' content"
        if isinstance(v, str):
            return [v]
        return v


class VSSUnit(BaseModel):
    definition: str
    unit: str | None
    quantity: str
    allowed_datatypes: list[str] | None = Field(alias="allowed-datatypes", default=None)

    @field_validator("quantity")
    @classmethod
    def check_valid_quantity(cls, v: str) -> str:
        assert v in dynamic_quantities, f"Invalid quantity: '{v}'"
        return v

    @field_validator("allowed_datatypes")
    @classmethod
    def check_valid_datatypes(cls, values: list[str]) -> list[str]:
        datatypes = get_all_datatypes()
        for value in values:
            assert value in datatypes, f"Invalid datatype: '{value}'"
        return values


class VSSQuantity(BaseModel):
    definition: str
    comment: str | None = None
    remark: str | None = None


class VSSDataDatatype(VSSData):
    datatype: str
    arraysize: int | None = None
    min: int | float | None = None
    max: int | float | None = None
    unit: str | None = None
    allowed: list[str | int | float | bool] | None = None
    default: list[str | int | float | bool] | str | int | float | bool | None = None

    @model_validator(mode="after")
    def check_type_arraysize_consistency(self) -> Self:
        """
        Checks that arraysize is only set when
        datatype is an array
        """
        if self.arraysize is not None:
            assert is_array(self.datatype), f"'arraysize' set on a non array datatype: '{self.datatype}'"
        return self

    @model_validator(mode="after")
    def check_type_default_consistency(self) -> Self:
        """
        Checks that the default value
        is consistent with the given datatype
        """
        if self.default is not None:
            if is_array(self.datatype):
                assert isinstance(
                    self.default, list
                ), f"'default' with type '{type(self.default)}' does not match datatype '{self.datatype}'"
                if self.arraysize:
                    assert len(self.default) == self.arraysize, "'default' array size does not match 'arraysize'"
                for v in self.default:
                    assert Datatypes.is_datatype(v, self.datatype), f"'{v}' is not of type '{self.datatype}'"
            else:
                assert not isinstance(
                    self.default, list
                ), f"'default' with type '{type(self.default)}' does not match datatype '{self.datatype}'"
                assert Datatypes.is_datatype(
                    self.default, self.datatype
                ), f"'{self.default}' is not of type '{self.datatype}'"
        return self

    @model_validator(mode="after")
    def check_default_values_allowed(self) -> Self:
        """
        Checks that the given default values
        are in the allowed list
        """
        if self.default and self.allowed:
            values = self.default
            if not isinstance(self.default, list):
                values = [self.default]
            for v in values:  # type: ignore
                assert v in self.allowed, f"default value '{v}' is not in 'allowed' list"
        return self

    @model_validator(mode="after")
    def check_allowed_datatype_consistency(self) -> Self:
        """
        Checks that allowed values are valid
        datatypes
        """
        if self.allowed:
            for v in self.allowed:
                assert Datatypes.is_datatype(v, self.datatype), f"'{v}' is not of type '{self.datatype}'"
        return self

    @model_validator(mode="after")
    def check_allowed_min_max(self) -> Self:
        err = "'min/max' and 'allowed' cannot be used together"
        if self.allowed is not None:
            assert self.min is None and self.max is None, err
        if self.min is not None or self.max is not None:
            assert self.allowed is None, err
        return self

    @model_validator(mode="after")
    def check_datatype(self) -> Self:
        assert self.datatype in get_all_datatypes(self.fqn), f"'{self.datatype}' is not a valid datatype"
        self.datatype = resolve_datatype(self.datatype, self.fqn)
        return self

    @field_validator("unit")
    @classmethod
    def check_valid_unit(cls, v: str | None) -> str | None:
        if v is None:
            return v
        assert v in dynamic_units, f"'{v}' is not a valid unit"
        return v

    @model_validator(mode="after")
    def check_datatype_matching_allowed_unit_datatypes(self) -> Self:
        """
        Checks that the datatype conforms to the allowed-datatypes
        referenced in the unit if given
        """
        if self.unit:
            assert Datatypes.get_type(self.datatype), f"Cannot use 'unit' with complex datatype: '{self.datatype}'"
            assert any(
                Datatypes.is_subtype_of(self.datatype.rstrip("[]"), a) for a in dynamic_units[self.unit]
            ), f"'{self.datatype}' is not allowed for unit '{self.unit}'"
        return self


class VSSDataProperty(VSSDataDatatype):
    pass


class VSSDataSensor(VSSDataDatatype):
    pass


class VSSDataActuator(VSSDataDatatype):
    pass


class VSSDataStruct(VSSData):
    pass


class VSSDataAttribute(VSSDataDatatype):
    pass


TYPE_CLASS_MAP = {
    NodeType.BRANCH: VSSDataBranch,
    NodeType.ATTRIBUTE: VSSDataAttribute,
    NodeType.SENSOR: VSSDataSensor,
    NodeType.ACTUATOR: VSSDataSensor,
    NodeType.STRUCT: VSSDataStruct,
    NodeType.PROPERTY: VSSDataProperty,
}


def resolve_vss_raw(model: VSSRaw) -> VSSData:
    """
    Resolves a raw model to the actual node that
    it should be validated to
    """
    model = VSSData(**model.model_dump())
    cls = TYPE_CLASS_MAP.get(model.type)
    if not cls:
        log.warning(f"No class mapping for type='{model.type.value}'")
        raise ModelException()
    model = cls(**model.model_dump())
    return model  # type: ignore


def get_vss_raw(data: dict[str, Any], fqn: str | None) -> VSSRaw:
    """
    Tries to build a VSSNode and falls back to the
    raw node
    """
    model = VSSRaw(fqn=fqn, **data)
    try:
        model = resolve_vss_raw(model)
    except (ValidationError, ModelException):
        log.debug(f"'{fqn}', incomplete, initialized as '{model.__class__.__name__}'")
        return model
    return model


def get_all_model_fields() -> list[str]:
    fields = set()
    for c in TYPE_CLASS_MAP.values():
        for k in c.model_fields.keys():  # type: ignore
            fields.add(k)
    log.debug(f"Core model, fields={len(fields)}")
    return list(fields)
