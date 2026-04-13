# VHAL Exporter

The VHAL exporter maps the VSS tree to Android VHAL properties by creating or modifying given map file and generating
needed Java and AIDL sources.

The Android VHAL property ID is composed of 4 parts (0xGATTDDDD):

- [Group](https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl): 1 nibble
- [Area](https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleArea.aidl): 1 nibble
- [Type](https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyType.aidl): 1 byte
- iDentifier: 2 bytes - as sequence (max 65535)

This mapper can create all group of properties defined in
[VehiclePropertyGroup](https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl)
and one additional we call OEM to demonstrate the possibility of a OEM specific scope (group).

## Property Change Mode

Each VHAL property has one of the following change modes:

STATIC
: used to VSS node types ATTRIBUTE.

ON_CHANGE
: used for VSS node types ACTUATOR and SENSOR.

CONTINUOUS
: used for VSS node types ACTUATOR and SENSOR if the path of that VSS node is present in JSON file provided by `--continuous-change-mode`.
  This is because the generator has no way to determine if a VSS node of type ACTUATOR or SENSOR should be ON_CHANGE or
  CONTINUOUS. It relies on the user to provide that information by listing the paths of those VSS nodes that should be
  generated with CONTINUOUS change mode in a JSON file (see below).

### Continuous Change Mode List Example

`vss_continuous.json`:
```json
[
  "Vehicle.Speed",
  "Vehicle.TraveledDistance",
  "Vehicle.Powertrain.Range",
  "Vehicle.Powertrain.CombustionEngine.Speed",
  "Vehicle.OBD.EngineSpeed",
  "Vehicle.Powertrain.ElectricMotor.Speed",
  "Vehicle.Powertrain.CombustionEngine.EOT",
  "Vehicle.Powertrain.CombustionEngine.EngineOil.Temperature",
  "Vehicle.Powertrain.TractionBattery.StateOfCharge.CurrentEnergy",
  "Vehicle.Powertrain.FuelSystem.AbsoluteLevel",
  "Vehicle.Chassis.Axle.Row1.SteeringAngle",
  "Vehicle.Chassis.Axle.Row2.SteeringAngle",
  "Vehicle.Exterior.AirTemperature",
  "Vehicle.Powertrain.CombustionEngine.ECT",
  "Vehicle.Powertrain.CombustionEngine.EngineCoolant.Temperature",
  "Vehicle.Powertrain.ElectricMotor.CoolantTemperature",
  "Vehicle.Powertrain.ElectricMotor.EngineCoolant.Temperature",
  "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current",
  "Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeCurrent.DC",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeCurrent.Phase1",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeCurrent.Phase2",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeCurrent.Phase3",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeVoltage.DC",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeVoltage.Phase1",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeVoltage.Phase2",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeVoltage.Phase3",
  "Vehicle.Powertrain.TractionBattery.Charging.ChargeRate",
  "Vehicle.Powertrain.TractionBattery.Charging.TimeToComplete",
  "Vehicle.Powertrain.TractionBattery.Temperature.Average",
  "Vehicle.Chassis.Axle.Row1.Wheel.Left.Tire.Pressure",
  "Vehicle.Chassis.Axle.Row1.Wheel.Right.Tire.Pressure",
  "Vehicle.Chassis.Axle.Row2.Wheel.Left.Tire.Pressure",
  "Vehicle.Chassis.Axle.Row2.Wheel.Right.Tire.Pressure"
]
```

## Generator Example

This example is meant to be used with the OEM VHAL (see [aosp_vendor_car](https://github.com/COVESA/aosp_vendor_car)
and [aosp_platform-manifest](https://github.com/COVESA/aosp_platform-manifest) repository for more details). It also
assumes `ANDROID_BUILD_TOP` environment variable pointing to the root of AOSP workspace where the output files will be
generated. The path to the android workspace can also be provided via `--aosp-workspace-path` argument overriding the
`ANDROID_BUILD_TOP` environment variable.

Use `--property-group 4` to generate OEM VHAL properties. For ACTUATOR and SENSOR nodes that should use CONTINUOUS
change mode, pass a JSON path list via `--continuous-change-mode` (see example above).

The generator creates or updates the map file (optional `--vhal-map`) and generates Java/AIDL sources in
`ANDROID_BUILD_TOP`. On first run, the map file is created; later runs append new mappings without removing existing
ones, so you can rerun safely as VSS evolves.

Minimal example:
```bash
vspec export vhal \
 --vspec /path/to/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
 --property-group 4 \
 --continuous-change-mode vss_continuous.json
```

While you can use this generator to generate `SYSTEM` (`--property-group 1`) or `VENDOR` (`--property-group 2`)
properties, the main purpose of this tool is to generate `OEM` (`--property-group 4`) properties for the Android
Automotive platform.

With SYSTEM properties you need to make sure not to conflict
with existing ones in the platform, therefore the use of `--min-property-id` is needed when generating the map file
for the first time.

To only update properties, i.e., ignore all newly added VSS nodes to the spec add `--no-extend-new` argument.

## Test data

This module uses an excerpt of vspec files in `test/vspec/test_static_uids_vhal/vehicle_signal_specification/` as test
data. For this purpose it is not required that those vspec test files are up-to-date, and therefore those files do not
need to be updated when the upstream vspec files change. They test the generator with a fixed set of VSS nodes and their
corresponding expected generated properties. If you want to add more test cases, you can add more vspec files or update
existing ones in that directory.
