# CAN DBC Profile

This profile can be used to specify how VSS signals can be mapped to CAN signals defined in DBC.
For more information on DBC see this [tutorial](https://www.csselectronics.com/pages/can-dbc-file-database-intro).
This profiles is based on the mapping definined in the [Eclipse KUKSA project](https://github.com/eclipse-kuksa/kuksa-can-provider/blob/main/mapping/README.md).

The profile define two extended attributes, `vss2dbc` and `dbc2vss`.
The reason for this is that handling is different.
Exact semantics for the information is unless specified in this document up to the implementation.


## Mapping syntax

The syntax for a DBC definition of a signal (in an overlay) is specified below.

Syntax

```yaml
<VSS Signal name>:
  type: <VSS type>
  datatype: <VSS datatype>
  vss2dbc:
    signal: <DBC signal name>
    [transform: ...]
  dbc2vss:
    signal: <DBC signal name>
    [interval_ms: <interval in milliseconds>]
    [on_change: {true|false}]
    [transform: ...]
```

* `dbc2vss` shall be specified if there is a need to transform from DBC/CAN to VSS.
  It is assumed that tra
* `vss2dbc` shall be specified if there is a need to transform from VSS to DBC/CAN.

Specifying DBC signal name is mandatory. It must correspond to a DBC signal name defined in a DBC file.

The `transform` entry can be used to specify conversion between DBC and VSS representation.
If transform is not specified values will be transformed as is.

### dbc2vss

It is possible that a VSS-based system does not need to get updated signal values as frequent as they are sent on CAN.

`interval_ms` and `on_change` are optional and control under which conditions a value shall be forwarded.
The `interval_ms` value indicates the (minimum) interval between updates in milliseconds. A value of `1000` indicates that the VSS system wants at least 1000 milliseconds between each update.
The `on_change: true` argument specifies that the VSS signal only shall be sent if the DBC value has changed.

If both are given it shall be considered as an AND-criteria. An update will be sent if DBC value has changed and the given interval has passed.
If none of them are specified it corresponds to that the signal shall be sent as soon as value has changed, i.e. `on_change: true`.

### vss2dbc

For `vss2dbc` it is assumed that the used CAN-stack will control when a specific CAN-frame will be sent. Any change in VSS value should result in that the corresponding DBC value is updated, but will not necessarily result in that the correspinding CAN-frame will be transmitted.

### Math Transformation

A Math transformation can be defined by the `math` attribute.
It accepts [py-expression-eval](https://github.com/AxiaCore/py-expression-eval/) formulas as argument.
It is expected that the "from" value is represented as `x`.

When evaluating what transformation is needed one must study both the DBC signal and the VSS signal. An example is given below for mirror tilt of left mirror.

**DBC**

The signal `VCLEFT_mirrorTiltYPosition` provides mirror tilt.

```
SG_ VCLEFT_mirrorTiltYPosition : 41|8@1+ (0.02,0) [0|5] "V"  Receiver
```

An introduction to DBC file syntax can be found [here](https://www.csselectronics.com/pages/can-dbc-file-database-intro).
The specification above shows that on CAN the tilt is represented as 0-5 Volts.
The value is sent with a scaling of 0.02 and uses 8 bits, i.e. 5 Volts is transmitted as 250,
but that information is not needed when using the profile,
as the transformation defined in the DBC is performed automatically when CAN frames are read.
For the input to the mapping you will need to consider just a value between 0 and 5 V in this example.

**VSS**

The corresponding signal in VSS uses -100 percent to +100 percent as range and int8 as datatype:

```
Vehicle.Body.Mirrors.DriverSide.Tilt:
  datatype: int8
  unit: percent
  min: -100
  max: 100
  type: actuator
  description: Mirror tilt as a percent. 0 = Center Position. 100 = Fully Upward Position. -100 = Fully Downward Position.
  ```

With an assumptions that 5 Volts corresponds to fully upward (+100%) and 0 Volts corresponds to
fully downward (-100%) then one could define mapping like in the example below.

```yaml
  Vehicle.Body.Mirrors.DriverSide.Tilt:
  datatype: int8
  type: actuator
  dbc2vss:
    signal: VCLEFT_mirrorTiltYPosition
    interval_ms: 100
    transform:
      math: "floor((x*40)-100)"
```

I.e. 2 Volts corresponds to `(2*40)-100` = -20%.

### Mapping Transformation

A Mapping transformation can be specified with the `mapping` attribute.
It must consist of a list of `from`/`to` pairs like in the example below.
When a DBC value is received the feeder will look for a matching `from` value in the list,
and the corresponding `to` value will be sent to KUKSA.val.

```yaml
Vehicle.Powertrain.Transmission.CurrentGear:
  type: sensor
  datatype: int8
  dbc2vss:
    signal: DI_gear
    transform:
       mapping:
        - from: DI_GEAR_D
          to: 1
        - from: DI_GEAR_P
          to: 0
        - from: DI_GEAR_INVALID
          to: 0
        - from: DI_GEAR_R
          to: -1
```

If no matching value is found the signal shall be ignored.

The from/to values must be compatible with DBC and VSS type respectively.
Numerical values must be written without quotes.
For boolean signals `true` and `false` without quotes is recommended, as that is valid values in both Yaml and JSON.
If using Yaml (*.vspec) as source format quoting string values is optional.
Quotes may however be needed if the value otherwise could be misinterpreted as a [Yaml 1.1](https://yaml.org/type/bool.html)
literal. Typical examples are values like `yes` which is a considered as a synonym to `true`.
If using JSON all strings must be quoted.

