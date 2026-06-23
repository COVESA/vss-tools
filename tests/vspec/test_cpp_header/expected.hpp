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

enum class VssNodeType : uint8_t {
    kSensor = 0,
    kActuator,
    kAttribute,
    kBranch,
};

enum class VssDataType : uint8_t {
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

enum class VssCppType : uint8_t {
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

enum class VssUnit : uint8_t {
    kNone = 0,
    kKm,
};

struct VssSignal {
    const char* const path;
    VssNodeType type;
    VssDataType datatype;
    VssCppType cpp_type;
    VssUnit unit;
    const char* const description;
    double min_value;   // kNoValue if unset
    double max_value;   // kNoValue if unset
    const char* const* const allowed_values;  // null-terminated, or nullptr
    const char* const default_value;
};

constexpr VssSignal A_Speed = {
    "A.Speed",
    VssNodeType::kSensor,
    VssDataType::kFloat,
    VssCppType::kFloat,
    VssUnit::kKm,
    "Vehicle speed.",
    0.0,
    300.0,
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
    VssNodeType::kActuator,
    VssDataType::kString,
    VssCppType::kConstCharPtr,
    VssUnit::kNone,
    "Gear selection mode.",
    kNoValue,
    kNoValue,
    A_GearMode_kAllowed,
    nullptr,
};

constexpr VssSignal A_Count = {
    "A.Count",
    VssNodeType::kAttribute,
    VssDataType::kUint32,
    VssCppType::kUint32T,
    VssUnit::kNone,
    "A count attribute.",
    kNoValue,
    kNoValue,
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
