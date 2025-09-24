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
and one additional we call VSS to demonstrate the possibility of a VSS specific scope (group).

## Property Change Mode

Each VHAL property has one of the following change modes:

STATIC
: used to VSS node types ATTRIBUTE.

ON_CHANGE
: used for VSS node types ACTUATOR and SENSOR.

CONTINUOUS
: used for VSS node types ACTUATOR and SENSOR if the path of that VSS node is present in JSON file provided by `--continuous-change-mode`.

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

## Examples

To generate SYSTEM properties use the following command. With SYSTEM properties we need to make sure not to conflict
with existing ones in the platform, therefore the use of `--min-property-id` is needed when generating the map file
for the first time:

```bash
vspec export vhal \
 --vspec /path/to/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
 --min-property-id 32768 \
 --vhal-map vss_to_android_property_map.json \
 --continuous-change-mode vss_continuous.json \
 --output-dir /path/to/output
```

To only update SYSTEM properties, i.e. ignore all newly added VSS nodes to the spec add `--no-extend-new` argument:

```bash
vspec export vhal \
 --vspec /path/to/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
 --vhal-map vss_to_android_property_map.json \
 --continuous-change-mode vss_continuous.json \
 --output-dir /path/to/output \
 --no-extend-new
```

To generate VENDOR properties use the argument `--property-group 2`:

```bash
vspec export vhal \
 --vspec /path/to/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
 --property-group 2 \
 --vhal-map vss_to_android_property_map.json \
 --continuous-change-mode vss_continuous.json \
 --output-dir /path/to/output
```

To generate VHAL properties in custom VSS group use the argument `--property-group 4`:

```bash
vspec export vhal \
 --vspec /path/to/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
 --property-group 4 \
 --vhal-map vss_to_android_property_map.json \
 --continuous-list-change-mode vss_continuous.json \
 --output-dir /path/to/output/
```
