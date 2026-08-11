# C++ Header Exporter

The `cpp-header` exporter generates a single header-only `.hpp` file that encodes the VSS tree as `constexpr` C++ data structures. It is intended for embedded and MCU targets where no filesystem or JSON parser is available at runtime. The output requires only `<cstddef>`, `<cstdint>` and `<limits>`.

## Exporter Specific Arguments

### `--namespace`

C++ namespace that wraps all generated symbols. Defaults to `vss`.

### `--include-branches` / `--no-include-branches`

When `--include-branches` is set, branch nodes are emitted alongside leaf signals. By default only leaf signals are included.

### `--signal`

Restrict output to specific signal paths (dotted, `*` glob supported, e.g. `Vehicle.ADAS.*`). Repeatable — pass `--signal` multiple times to select several paths or patterns. Omit it to export every signal. If `--include-branches` is also set, only the ancestor branches of matched signals are included, not every branch in the tree — this keeps the output small for memory-constrained targets, which is the point of filtering in the first place.

```bash
vspec export cpp-header --vspec spec/VehicleSignalSpecification.vspec \
  --signal Vehicle.Speed --signal 'Vehicle.Body.Lights.*' \
  --output vss.hpp
```

## Output Structure

The generated header always contains:

- `NodeType`, `DataType`, `CppType` and `Unit` enums (`enum class ... : uint8_t`).
- A `Signal` struct with `path`, `type`, `datatype`, `cpp_type`, `unit`, `description`, `min_value`, `max_value`, `default_value`, and a null-terminated `allowed_values` pointer (or `nullptr`).
- One `constexpr Signal` per selected leaf signal. If the signal has `allowed:` values, a null-terminated `constexpr const char*[]` is emitted immediately above it.
- A `constexpr Signal kSignals[]` aggregate containing every emitted signal in pre-order.
- `constexpr std::size_t kSignalCount` derived from `kSignals`.

VSS datatypes are mapped to C++ types as follows (see `vss_tools.datatypes.Datatypes` for the authoritative datatype list):

| VSS datatype | C++ type |
|---|---|
| `uint8` / `int8` | `uint8_t` / `int8_t` |
| `uint16` / `int16` | `uint16_t` / `int16_t` |
| `uint32` / `int32` | `uint32_t` / `int32_t` |
| `uint64` / `int64` | `uint64_t` / `int64_t` |
| `float` | `float` |
| `double` | `double` |
| `boolean` | `bool` |
| `string` | `const char*` |
| `numeric` | `double` |
| `T[]` (array) | `const T*` (`const char* const*` for `string[]`) |

## Example

Input model:

```yaml
# model.vspec
Vehicle:
  type: branch
  description: High-level vehicle data.

Vehicle.Speed:
  type: sensor
  datatype: float
  unit: km
  min: 0
  max: 250
  description: Vehicle speed.

Vehicle.Powertrain:
  type: branch
  description: Powertrain data.

Vehicle.Powertrain.Type:
  type: attribute
  datatype: string
  allowed: [combustion, hybrid, electric]
  description: The powertrain type of the vehicle.
```

Generator call:

```bash
vspec export cpp-header --vspec model.vspec --output vss.hpp
```

Generated file:

```cpp
// SPDX-FileCopyrightText: Copyright (c) 2026 Contributors to COVESA
// SPDX-License-Identifier: MPL-2.0

// Auto-generated from the Vehicle Signal Specification.
// Do not edit manually.

#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace vss {

constexpr double kNoValue = std::numeric_limits<double>::quiet_NaN();

enum class NodeType : uint8_t {
    kSensor = 0,
    kActuator,
    kAttribute,
    kBranch,
};

enum class DataType : uint8_t {
    kUnknown = 0,
    kUint8,
    kInt8,
    kUint16,
    kInt16,
    kUint32,
    kInt32,
    kUint64,
    kInt64,
    kFloat,
    kDouble,
    kBoolean,
    kString,
    kUint8Array,
    kInt8Array,
    kUint16Array,
    kInt16Array,
    kUint32Array,
    kInt32Array,
    kUint64Array,
    kInt64Array,
    kFloatArray,
    kDoubleArray,
    kBooleanArray,
    kStringArray,
    kNumeric,
    kNumericArray,
};

enum class CppType : uint8_t {
    kUnknown = 0,
    kUint8T,
    kInt8T,
    kUint16T,
    kInt16T,
    kUint32T,
    kInt32T,
    kUint64T,
    kInt64T,
    kFloat,
    kDouble,
    kBool,
    kConstCharPtr,
    kConstUint8TPtr,
    kConstInt8TPtr,
    kConstUint16TPtr,
    kConstInt16TPtr,
    kConstUint32TPtr,
    kConstInt32TPtr,
    kConstUint64TPtr,
    kConstInt64TPtr,
    kConstFloatPtr,
    kConstDoublePtr,
    kConstBoolPtr,
    kConstCharConstPtr,
};

enum class Unit : uint8_t {
    kNone = 0,
    kKm,
};

struct Signal {
    const char* const path;
    NodeType type;
    DataType datatype;
    CppType cpp_type;
    Unit unit;
    const char* const description;
    double min_value;   // kNoValue if unset
    double max_value;   // kNoValue if unset
    const char* const* const allowed_values;  // null-terminated, or nullptr
    const char* const default_value;
};

constexpr Signal Vehicle_Speed = {
    "Vehicle.Speed",
    NodeType::kSensor,
    DataType::kFloat,
    CppType::kFloat,
    Unit::kKm,
    "Vehicle speed.",
    0.0,
    250.0,
    nullptr,
    nullptr,
};

constexpr const char* Vehicle_Powertrain_Type_kAllowed[] = {
    "combustion",
    "hybrid",
    "electric",
    nullptr,
};
constexpr Signal Vehicle_Powertrain_Type = {
    "Vehicle.Powertrain.Type",
    NodeType::kAttribute,
    DataType::kString,
    CppType::kConstCharPtr,
    Unit::kNone,
    "The powertrain type of the vehicle.",
    kNoValue,
    kNoValue,
    Vehicle_Powertrain_Type_kAllowed,
    nullptr,
};

constexpr Signal kSignals[] = {
    Vehicle_Speed,
    Vehicle_Powertrain_Type,
};

constexpr std::size_t kSignalCount = sizeof(kSignals) / sizeof(kSignals[0]);

}  // namespace vss
```

The header is self-contained and can be compiled without any vss-tools dependency:

```bash
g++ -std=c++17 -c vss.hpp
```

*(This example, including the generated output above, is verified against the exporter as part of the test suite — see `tests/vspec/test_cpp_header/`.)*
