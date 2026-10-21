# Vspec SysML v2 Exporter

This vspec exporter is used to export a VSS file to SysML v2.
*Developed in the context of HAL4SDV, contact ansgar.radermacher@cea.fr*

## Why?
- Link with OMG standard [SysML](https://www.omg.org/spec/SysML/), access from tools used in automotive
- SysML models (architecture, etc.) can access VSS definitions
- Use of SysML v2 textual format as exchange format

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
  - Branch = package (optional) + part definition
  - Instance: several options, see next page. Quite complex for nested instances

- Naming conventions

  - Branch
    - Unmodified name for part definition, contained in package with “P” prefix
	  (Discussion: use attribute definition instead of part definition?)
    - Attribute in parent part definition, first character lower-case
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
part def Body {
  front : Windshield
  rear : Windshield
  ...
}

part def Windshield {
  wiping : Wiping
  ...
}
```

Option2, use an additional part definition representing the instance specification. This is closer to original tree:

```
part def Body {
  windshield : WindshieldIS
  ...
}

part def WindshieldIS {
  front : Windshield
  rear : Windshield
}

part def Windshield {
  wiping : Wiping
  ...
}
```

The current SysML v2 export implements the second option

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
vspec export sysmlv2 --vspec <VSS specification> --output <output file>
```
