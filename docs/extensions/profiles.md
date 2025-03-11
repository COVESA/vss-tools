# Profiles


## Introduction

The concept of extended attributes has existed for a quite long time in vss-tools. This gives a possibility to use extended attributes in a VSS tree and instruct vss-tools to accept those additional attributes and depending on target format represent them in the output format.

A simple example could be:

```yaml
Vehicle.Speed:
    type: sensor
    unit: "km/h"
    datatype: float
    quality: 100
    source: "ecu0xAA"
```


A more complex example could be:

```yaml
Vehicle.Speed:
    type: sensor
    unit: "km/h"
    datatype: float
    quality: 100
    source:
      xpos:
        - a: 123
          b: 245
        - a: 876
          b: 654
      ypos: 45
```

By specifying `-e source -e quality` the source attribute will for example be present in the JSON representation of the VSS model.
Vss-tools does however not know how the `source` and `quality` attributes are supposed to be used and what they are supposed to contain.
Vss-tools profiles is an attempt to give a more formal definition to extended attributes.
That allows vss-tools or downstream tools to implement syntactial/semantical checks on that the attributes are correctly used.
It also serves as a documentation format for the extended attributes.

*NOTE: As of today vss-tools does not support parsing or interepretation of vss-tools profiles. You still need to specify the attributes with `-e`!*

## Syntax

A possible syntax is described below, allowing to define base type of the attribute and for which nodes the extended attributes must be used.

```yaml
  {
  <extended attribute identifier>:
    [mandatory: {True|False}] # default False
    [list: {True|False}] # default False
    [unit: <vss-unit>] # default: Undefined
    [datatype: <vss-datatype>] # default: Undefined
    [allowed: <array of allowed values>] # default: Undefined
    [default: <value>] # default: Undefined, not relevant if mandatory
    [min: <value>] # default: Implied by datatype
    [max: <value>] # default: Implied by datatype
    [definition: <free text>] # Longer free text definition
    [description: <free text>]

  }*


```

A hypothetical example for the more complex `Vehicle.Speed` example above could be:

```yaml
  source:
    mandatory: true
    description: "Gives some info"
    xpos:
      list: True # Indicates that children may be in a list
      a:
        datatype: uint8
        description "A value"
      b:
        datatype: uint8
        description "B value"
    ypos:
      datatype: uint8
      description "Y value"
  quality:
    datatype: uint8
    description "Q value"
```

The profile could then be applied like `-p myprofile.yml`

If applied, all attributes, sensors and actuators, must use the `source` attribute, but `quality`is optional.

*It may however be difficult to express all possible allowed combinations!*
*Alternatively one could just represent top level elements!*

## Profile Library

Profiles may be defined within the VSS-project or by downstream projects.
As of today the profiles definined within the VSS-project shall be seen as contributed proposals on how VSS can be extended for specific purposes. They shall as of today not be seen as "standardized profiles" or "recommended profiles".
They are considered as an add-on to VSS rather than a core part of VSS, and that is why they are documented as part of vss-tools rather as part of official [VSS documentation](https://covesa.github.io/vehicle_signal_specification/).



* [CAN DBC Profile](can.md) - A profile defining mapping between CAN and DBC

## Profile Support in VSS-tools

As of today vss-tools does not support profiles. You need to pass relevant extra attributes with `-e`.
Future possible improvements include

* Injection and parsing of profiles and assuring that they are correctly used.
* Extending profile support in VSS-tooling. As of today extended attributes can be reflected in general purpose exporters like yaml and json, and some CSV support is [coming](https://github.com/COVESA/vss-tools/pull/438).
