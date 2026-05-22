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

constexpr VssSignal A_Speed = {
    "A.Speed",
    "sensor",
    "float",
    "float",
    "km",
    "Vehicle speed.",
    "0",
    "300",
    nullptr,
    nullptr,
};

constexpr const char* A_GearMode_kAllowed[] = {
    "PARK",
    "REVERSE",
    "NEUTRAL",
    "DRIVE",
    nullptr,
};
constexpr VssSignal A_GearMode = {
    "A.GearMode",
    "actuator",
    "string",
    "const char*",
    nullptr,
    "Gear selection mode.",
    nullptr,
    nullptr,
    A_GearMode_kAllowed,
    nullptr,
};

constexpr VssSignal A_Count = {
    "A.Count",
    "attribute",
    "uint32",
    "uint32_t",
    nullptr,
    "A count attribute.",
    nullptr,
    nullptr,
    nullptr,
    "0",
};

constexpr VssSignal kSignals[] = {
    A_Speed,
    A_GearMode,
    A_Count,
};

constexpr std::size_t kSignalCount = sizeof(kSignals) / sizeof(kSignals[0]);

}  // namespace vss
