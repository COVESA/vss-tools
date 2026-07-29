# C++ Header Exporter

The `cpp-header` exporter generates a single header-only `.hpp` file that encodes the VSS tree as `constexpr` C++ data structures. It is intended for embedded and MCU targets where no filesystem or JSON parser is available at runtime. The output requires only `<cstddef>` and `<cstdint>`.

## Exporter Specific Arguments

### `--namespace`

C++ namespace that wraps all generated symbols. Defaults to `vss`.

### `--include-branches` / `--no-include-branches`

When `--include-branches` is set, branch nodes are emitted alongside leaf signals. By default only leaf signals are included.

## Output Structure

The generated header always contains:

- A `VssSignal` struct with string fields for `path`, `type`, `datatype`, `cpp_type`, `unit`, `description`, `min_value`, `max_value`, `default_value`, and a null-terminated `allowed_values` pointer (or `nullptr`).
- One `constexpr VssSignal` per leaf signal. If the signal has `allowed:` values, a null-terminated `constexpr const char*[]` is emitted immediately above it.
- A `constexpr VssSignal kSignals[]` aggregate containing every signal in pre-order.
- `constexpr std::size_t kSignalCount` derived from `kSignals`.

VSS datatypes are mapped to C++ types as follows:

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
| `T[]` (array) | `const T*` |

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
  unit: km/h
  min: 0
  max: 250
  description: Vehicle speed.

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

Generated file (excerpt):

```cpp
// SPDX-FileCopyrightText: Copyright (c) 2024 Contributors to COVESA
// SPDX-License-Identifier: MPL-2.0

// Auto-generated from the Vehicle Signal Specification.
// Do not edit manually.

#pragma once

#include <cstddef>
#include <cstdint>

namespace vss {

struct VssSignal {
    const char* const path;
    const char* const type;
    const char* const datatype;
    const char* const cpp_type;
    const char* const unit;
    const char* const description;
    const char* const min_value;
    const char* const max_value;
    const char* const* const allowed_values;  // null-terminated, or nullptr
    const char* const default_value;
};

constexpr VssSignal Vehicle_Speed = {
    "Vehicle.Speed",
    "sensor",
    "float",
    "float",
    "km/h",
    "Vehicle speed.",
    "0",
    "250",
    nullptr,
    nullptr,
};

constexpr const char* Vehicle_Powertrain_Type_kAllowed[] = {
    "combustion",
    "hybrid",
    "electric",
    nullptr,
};
constexpr VssSignal Vehicle_Powertrain_Type = {
    "Vehicle.Powertrain.Type",
    "attribute",
    "string",
    "const char*",
    nullptr,
    "The powertrain type of the vehicle.",
    nullptr,
    nullptr,
    Vehicle_Powertrain_Type_kAllowed,
    nullptr,
};

constexpr VssSignal kSignals[] = {
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
