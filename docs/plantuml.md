# Vspec PlantUML Exporter

### developed in the context of HAL4SDV, contact ansgar.radermacher@cea.fr

This vspec exporter is used to export a VSS file to PlantUML

## Why?
- Link with OMG standard [UML](https://www.omg.org/spec/UML/), access from tools used in automotive
- UML models (architecture, etc.) can access VSS definitions
- Use of PlantUML as simple exchange format (even if not fully compliant)

## Mapping Objectives

- VSS is a hierarchical decomposition, not only on namespace/package level, but also on instance level
- No name clashes
- Not bijective
- Keep it simple:
  - Avoid duplication, if possible
  -  Use adequate language elements
  - Human readable


## Handling of instances
- Need to distinguish between branch and instance
  - Instances are not namespaces – should not be mapped to packages (DDSIDL does)
  - Branch = package (optional) + composite class
  - Instance: several options, see next page. Quite complex for nested instances

- Naming conventions

  - Branch
    - Unmodified name for composite class, contained in package with “P” prefix
    - Attribute in parent class, first character lower-case
  - Enums (see later): unmodified name (use E prefix?)


### Example

```
Windshield:
  type: branch
  instances: ["Front", "Rear"]
  description: Windshield signals.
```


Option1, instances become attributes of parent node (“polluting”):

```
class Body {
  front : Windshield
  rear : Windshield
  ...
}

class Windshield {
  wiping : Wiping
  ...
}
```

Option2, use an additional class representing the instance specification. This is closer to original tree:

```
class Body {
  windshield : WindshieldIS
  ...
}

class WindshieldIS {
  front : Windshield
  rear : Windshield
}

class Windshield {
  wiping : Wiping
  ...
}
```

The current PlantUML export implements the second option

## Mapping of allowed values => Enumerations

Some values have fixed set of allowed values, can be mapped to enumerations (as done for instance already by DDS-IDL export)

- Issue: no type level, definition in context of typed-element → duplication
- Solved via #include and a given EntryPoint in VSS spec, but duplicated in export
- Switch in Cabin.Sunroof has two additional literals TILT_UP and TILT_DOWN
- Use of inheritance in future revisions?
- EngineOilLevel vs. Level with identical literals

=> Accept limited duplication for the moment (8x Switch)

=> Identify identical enumerations via literal comparison?

## Usage

```
vspec export plantuml --vspec <VSS specification> --output <output file>
```
