# ROS 2 Interface Exporter (`ros2interface`)

Exports a VSS model to a ROS 2 interface package: generates `.msg` files (per leaf or aggregated by parent branch) and optional `.srv` files for latest-single-value Get/Set operations, time-range (timeseries) Get/Set operations, and timeseries deletion.
This exporter plugs into the `vspec export` CLI like other vss-tools exporters. For generic exporter usage and common arguments, see the `vspec` documentation.

## Generated Output Structure
```
\<output>
└── <package-name>
    ├── msg  # generated .msg definitions
    |   ├── \<Msg>.msg
    |   └── \<Msg>Timeseries.msg              # only when --timeseries is used
    └── srv  # generated .srv (if a service option is enabled)
        ├── Get\<Msg>.srv                     # only when --srv get|both
        ├── Set\<Msg>.srv                     # only when --srv set|both
        ├── Get\<Msg>Timeseries.srv           # only when --timeseries get|both
        ├── Set\<Msg>Timeseries.srv           # only when --timeseries set|both
        └── Delete\<Msg>Timeseries.srv        # only when --timeseries-delete is set
```

**Example Output**

```
OutputFolder
└── Vss-Interface
    ├── msg
    |   ├── VehicleSpeed.msg
    |   └── VehicleSpeedTimeseries.msg
    └── srv
        ├── GetVehicleSpeed.srv
        ├── SetVehicleSpeed.srv
        ├── GetVehicleSpeedTimeseries.srv
        ├── SetVehicleSpeedTimeseries.srv
        └── DeleteVehicleSpeedTimeseries.srv
```

- .msg files include VSS metadata as comments (description, unit, min/max, allowed values).
- Optional latest-single-value .srv files (Get\<Msg>.srv, Set\<Msg>.srv)
- When `--timeseries get|set|both` is enabled, per-signal `<Msg>Timeseries.msg` and the matching `Get<Msg>Timeseries.srv` / `Set<Msg>Timeseries.srv` are emitted, for service-based batch retrieval and injection of stamped samples over a time range.
- When `--timeseries-delete` is enabled, a `Delete<Msg>Timeseries.srv` is emitted, for full or partial deletion of stored samples.


## Datatypes mapping between VSS and ROS 2 Interface

| VSS    | ROS 2          |
|--------|----------------|
| boolean| bool           |
| uint8  | uint8          |
| int8   | int8           |
| uint16 | uint16         |
| int16  | int16          |
| uint32 | uint32         |
| int32  | int32          |
| uint64 | uint64         |
| int64  | int64          |
| float  | float32        |
| double | float64        |
| string | string         |


## Command Options

### Core

- `--output <dir>`: Output directory (required).
- `--package-name <name>`: Name of generated ROS 2 interface package (default: `vss_interfaces`).
- `--mode {aggregate, leaf}`:
  - `aggregate`: one `.msg` per direct parent branch containing all of its leaf signals.
  - `leaf`: one `.msg` per leaf signal.
- `--srv {get, set, both}`: Generate latest-single-value `.srv` files.
  - `get`:
    - creates `Get<Msg>.srv` files to retrieve the latest single value (empty request, single-value response).
  - `set`:
    - creates `Set<Msg>.srv` files to send a single value and get `success` as response if the data gets saved.
  - `both`:
    - creates both the `Get<Msg>.srv` and `Set<Msg>.srv` files.
- `--srv-use-msg / --no-srv-use-msg`: In services, use the generated message as a nested field (default: `--srv-use-msg`); otherwise flatten fields.
- `--timeseries {get, set, both}`: Generate time-range (timeseries) `.srv` files plus the shared `<Msg>Timeseries.msg` wrapper.
  - `get`:
    - creates `<Msg>Timeseries.msg` + `Get<Msg>Timeseries.srv` to retrieve a batch of stamped samples over a time window.
  - `set`:
    - creates `<Msg>Timeseries.msg` + `Set<Msg>Timeseries.srv` to inject a batch of stamped samples.
  - `both`:
    - creates the wrapper `.msg` and both timeseries services.
  - Composes with `--timestamp-struct-fqn` and is independent of `--srv`. See [Timeseries](#timeseries----timeseries) in the Output section.
- `--timeseries-delete`: Generate a `Delete<Msg>Timeseries.srv` for deleting stored samples. The service is mode-based: `FULL` (delete all), `TIME_WINDOW` (delete a `[start, end]` range), or `RETENTION_FLOOR` (keep at least N most-recent). Destructive, so off by default. Composes with `--timestamp-struct-fqn` and `--timeseries`. See [Timeseries Deletion](#timeseries-deletion----timeseries-delete) in the Output section.
- `--timestamp-struct-fqn <fqn>`: Full FQN of the timestamp struct in the types tree loaded via `--types`. If not provided, falls back to built-in defaults.
- `--output-vspec <file>`: Path to write a transformed VSS model alongside the ROS 2 package. See [Transformed VSS](#transformed-vss-vspec----output-vspec) in the Output section.

### Topic/Signal Selection

- `--topics PATTERN` (repeatable): Include filter patterns.
- `--exclude-topics PATTERN` (repeatable): Exclude filter patterns.
- `--topics-file <file>`: File with one pattern per line; `#` starts a comment.
- `--topics-case-insensitive / --topics-case-sensitive`: Case-insensitive matching (default: `--topics-case-sensitive`).

**Pattern syntax**

Following patterns are supported:

- Exact FQN: `Vehicle.Speed`
- Leaf name: `Speed`
- Glob: `Vehicle.*.Speed`, `*.Speed`
- Explicit prefix`:
  - regex: `^Vehicle\.Body\..*$`
  - glob: `*.Speed`
  - fqn: `Vehicle.Speed` (exact or prefix match)
  - Name: `Speed`

## Output

### Timestamp fields

Timestamp fields come from the struct identified by `--timestamp-struct-fqn` in the types tree loaded via `--types`.
If found, the struct's direct `property` children become the leading timestamp fields in every `.msg` (and the window/range fields in timeseries `.srv` files).
When --timestamp-struct-fqn is not provided, the exporter falls back to built-in defaults; and if the struct is not found, an error is raised.

|`--types`|`--timestamp-struct-fqn`|Result|
|-|-|-|
|none|none|use built-in defaults|
|none|any|Error(invalid option combination)|
|any|none|use built-in defaults|
|any|any|use that struct(if not found, Error)|

```
int64 timestamp_seconds
int64 timestamp_nanoseconds
```

### Messages (`.msg`)

- `Aggregate` mode
  one message per direct parent branch. Fields include leading `int64 timestamp_seconds` / `int64 timestamp_nanoseconds` fields, then one field per child leaf.

- `Leaf` mode
  one message per leaf. Fields include timestamp fields followed by a `value` field for the leaf value.

**Example — `VehicleSpeed.msg`**
```
# AUTO-GENERATED by VSS-TOOLS
# Signal: Vehicle.Speed

# Unix epoch seconds; unit=unix-time
int64 timestamp_seconds

# Nanoseconds [0, 999999999]
int64 timestamp_nanoseconds

# Vehicle speed.; unit=km/h
float32 value
```

### Latest-single-value Services (`--srv`)

Generated when `--srv get|set|both` is used. These services operate on the **latest single value** of a signal.

- `Get<Msg>.srv`
  - Request: empty — the service always returns the latest single value, so no time window is needed.
  - Response: `<Msg> data` (with `--srv-use-msg`) or flattened fields.

- `Set<Msg>.srv`
  - Request: `<Msg> data` (with `--srv-use-msg`) or flattened fields.
  - Response: `bool success`, `string message`.

**Example — `GetVehicleSpeed.srv`**
```
# AUTO-GENERATED by VSS-TOOLS
# Service: GetVehicleSpeed

# Returns the latest single value for this group.
---
VehicleSpeed data   # Latest data
```

**Example — `SetVehicleSpeed.srv`**
```
# AUTO-GENERATED by VSS-TOOLS
# Service: SetVehicleSpeed

# Sets the latest single value for this group.
VehicleSpeed data
---
bool success
string message
```

### Timeseries (`--timeseries`)

When `--timeseries get|set|both` is set, the exporter emits the shared `<Msg>Timeseries.msg` wrapper plus the selected service files, alongside the per-signal point-in-time `<Msg>.msg`. Unlike the latest-single-value Get above, the timeseries Get carries a **time-window** request:

- `<Msg>Timeseries.msg` — variable-length array of stamped samples with window metadata. Emitted for any `--timeseries` value (shared by Get and Set).
  - Fields: `window_start_<suffix>` / `window_end_<suffix>` (one pair per timestamp property), followed by `<Msg>[] samples`.
- `Get<Msg>Timeseries.srv` (`get` or `both`) — batch retrieval over a time window.
  - Request: `start_time_<suffix>` / `end_time_<suffix>` fields, `uint32 max_samples` (0 = unlimited), `bool prefer_newest` (server retention policy when the window contains more samples than `max_samples`).
  - Response: `<Msg>Timeseries timeseries`, `bool success`, `string message`.
- `Set<Msg>Timeseries.srv` (`set` or `both`) — batch injection.
  - Request: `<Msg>Timeseries timeseries`, `bool prefer_newest` (server drop policy when the injected batch exceeds buffer capacity).
  - Response: `bool success`, `string message`, `uint32 samples_accepted` (for partial-acceptance reporting).

The timestamp suffixes (`window_start_<suffix>`, `start_time_<suffix>`, ...) inherit from the resolved timestamp schema, so `--timestamp-struct-fqn` composes transparently — a custom timestamp struct flows into the timeseries types without further configuration. `--timeseries` is independent of `--srv`: the two take the same `get|set|both` selector and can be combined, with `--srv` controlling the latest-single-value services and `--timeseries` controlling the time-range services.

**Example — `VehicleSpeedTimeseries.msg`**
```
# AUTO-GENERATED by VSS-TOOLS
# Timeseries wrapper for VehicleSpeed

# Inclusive window start
int64 window_start_seconds

# Inclusive window start
int64 window_start_nanoseconds

# Inclusive window end
int64 window_end_seconds

# Inclusive window end
int64 window_end_nanoseconds

# Ordered ascending by sample timestamp
VehicleSpeed[] samples
```

**Example — `GetVehicleSpeedTimeseries.srv`**
```
# AUTO-GENERATED by VSS-TOOLS
# Service: GetVehicleSpeedTimeseries

# Retrieves a batch of stamped samples for this signal over a time window.
int64 start_time_seconds
int64 start_time_nanoseconds
int64 end_time_seconds
int64 end_time_nanoseconds
uint32 max_samples  # 0 = unlimited
bool prefer_newest  # true = fetch newest when window exceeds max_samples; false = fetch oldest. Ignored when max_samples == 0.
---
VehicleSpeedTimeseries timeseries
bool success
string message
```

**Example — `SetVehicleSpeedTimeseries.srv`**
```
# AUTO-GENERATED by VSS-TOOLS
# Service: SetVehicleSpeedTimeseries

# Injects a batch of stamped samples into this signal's server-side buffer.
VehicleSpeedTimeseries timeseries
bool prefer_newest  # true = drop oldest when injected batch exceeds buffer; false = drop newest (reject incoming once full).
---
bool success
string message
uint32 samples_accepted  # how many samples were actually stored
```

Timeseries messages are intended primarily as service payloads (batch retrieval for downstream statistics, replay, or cloud-upload pipelines), rather than as primary Pub/Sub topics — the per-signal `<Msg>.msg` continues to serve the Pub/Sub leg. The `prefer_newest` field on both Get and Set requests makes the sample-retention/drop policy an explicit client choice rather than a server default, so behavior is consistent across implementations.

### Timeseries Deletion (`--timeseries-delete`)

When `--timeseries-delete` is set, the exporter emits a single `Delete<Msg>Timeseries.srv` per signal. Deletion is **destructive** and therefore off by default; it is a dedicated opt-in flag so destructive operations stay easy to audit.

A single mode-based service covers both full and partial deletion. The `mode` field is authoritative — fields that do not apply to the chosen mode are ignored.

- `Delete<Msg>Timeseries.srv`
  - Request:
    - `uint8 mode` — `0 = FULL`, `1 = TIME_WINDOW`, `2 = RETENTION_FLOOR`.
    - `start_time_<suffix>` / `end_time_<suffix>` — used when `mode == 1 (TIME_WINDOW)` : delete samples whose timestamp falls in `[start, end]`.
    - `uint32 keep_latest` — used when `mode == 2 (RETENTION_FLOOR)` : delete oldest samples while retaining at least this many of the most recent.
  - Response:
    - `bool success`, `string message`.
    - `uint32 samples_deleted` — how many samples were actually removed.
    - `uint32 samples_retained` — how many remain after the operation.

| `mode` | Name | Behavior | Window fields | `keep_latest` |
|---|---|---|---|---|
| `0` | `FULL` | Delete all stored samples for the signal. | ignored | ignored |
| `1` | `TIME_WINDOW` | Delete samples whose timestamp is within `[start, end]` (inclusive). | used | ignored |
| `2` | `RETENTION_FLOOR` | Delete oldest samples but retain at least `keep_latest` of the most recent. | ignored | used |

The `RETENTION_FLOOR` mode covers the "reduce capacity but keep a legal minimum" use case: a client requests deletion while guaranteeing that at least `keep_latest` of the most recent samples remain. The `samples_retained` response field lets the client confirm the floor was honored (i.e. `samples_retained >= keep_latest`). The `start_time_<suffix>` / `end_time_<suffix>` window fields inherit from the resolved timestamp schema, so `--timestamp-struct-fqn` composes transparently here too.

Deleting zero matching samples is **not** a failure: `success` is `true` with `samples_deleted = 0` (idempotent — deleting an already-empty range is a no-op).

**Example — `DeleteVehicleSpeedTimeseries.srv`**
```
# AUTO-GENERATED by VSS-TOOLS
# Service: DeleteVehicleSpeedTimeseries

# Deletes stored samples for this signal (full, time-window, or retention-floor).
# constants for mode
uint8 FULL=0                  # full delete of all samples
uint8 TIME_WINDOW=1           # delete only those that coincide between the selected time window
uint8 RETENTION_FLOOR=2       # Minimum samples to retain

uint8 mode                    # deletion mode (FULL, TIME_WINDOW, or RETENTION_FLOOR)
int64 start_time_seconds      # used when mode == 1 (TIME_WINDOW)
int64 start_time_nanoseconds  # used when mode == 1 (TIME_WINDOW)
int64 end_time_seconds        # used when mode == 1 (TIME_WINDOW)
int64 end_time_nanoseconds    # used when mode == 1 (TIME_WINDOW)
uint32 keep_latest            # used when mode == 2 (RETENTION_FLOOR): min most-recent samples to retain
---
bool success
string message
uint32 samples_deleted        # how many samples were actually removed
uint32 samples_retained       # how many remain after the operation
```

### Transformed VSS (`.vspec`) — `--output-vspec`

When `--output-vspec <file>` is provided, a transformed VSS model is written alongside the ROS 2 package. Each selected signal is restructured as:

```yaml
# Branch intermediaries are preserved
Vehicle:
  type: branch

Vehicle.Speed:
  type: struct

Vehicle.Speed.Time:
  type: property
  datatype: <timestamp-struct-fqn>   # the FQN given via --timestamp-struct-fqn

Vehicle.Speed.Value:
  type: sensor
  datatype: float
  description: Vehicle speed.
  unit: km/h
```

The timestamp struct itself is **not** re-emitted — it is expected to already be present in the types tree.

## Examples

- Export only Vehicle.Speed as leaf message + latest-single-value get/set services:

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_speed_interfaces \
  --mode leaf \
  --srv both --srv-use-msg \
  --topics Vehicle.Speed

```
- Export all *.Speed signals, aggregated by their parent branches:

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_speed_agg \
  --mode aggregate \
  --srv get \
  --topics '*.Speed'
```
- Export with a custom timestamp struct from the types tree:

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --types path/to/MyTypes.vspec \
  --output ./out \
  --package-name vss_interfaces \
  --mode leaf \
  --srv both --srv-use-msg \
  --timestamp-struct-fqn MyTypes.Timestamp
```
- Exports and writes a transformed VSS model.
  - Each signal becomes `<Signal>.Time` with datatype set to the FQN given via `--timestamp-struct-fqn`
  - and `<Signal>.Value` carrying the original datatype.
  - The timestamp struct itself is NOT re-emitted.

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_interfaces \
  --mode leaf \
  --output-vspec ./out/transformed.vspec
```
- Export Vehicle.Speed with timeseries support (batch retrieval + injection services and the wrapper message, in addition to the point-in-time message):

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_speed_interfaces \
  --mode leaf \
  --topics Vehicle.Speed \
  --timeseries both
```

- Export Vehicle.Speed with both latest-single-value and timeseries services:
  - This produces `VehicleSpeed.msg`, `GetVehicleSpeedTimeseries.srv`, and `SetVehicleSpeedTimeseries.srv`
  - The latest-single-value `GET`/`SET` services are still gated by `--srv` CLI flag independently.

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_speed_interfaces \
  --mode leaf \
  --topics Vehicle.Speed \
  --srv get \
  --timeseries both
```

- Export Vehicle.Speed with a timeseries delete service (full / partial deletion):
  - This produces `VehicleSpeed.msg` and `DeleteVehicleSpeedTimeseries.srv`.
  - Can be combined with `--timeseries get|set|both` to also generate the retrieval/injection services.

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --output ./out \
  --package-name vss_speed_interfaces \
  --mode leaf \
  --topics Vehicle.Speed \
  --timeseries-delete
```

**Full example using the `vehicle_signal_specification` repo side-by-side with `vss-tools`:**

Assumes the following folder layout:

> ```
> <parent-folder>/
> ├── vehicle_signal_specification/
> └── vss-tools/
> ```

Adjust paths accordingly if your layout differs.

```bash
vspec export ros2interface \
  --vspec ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
  -I ../vehicle_signal_specification/spec/include \
  --types ../vehicle_signal_specification/spec/VehicleDataTypes.vspec \
  -q ../vehicle_signal_specification/spec/quantities.yaml \
  -u ../vehicle_signal_specification/spec/units.yaml \
  --output ./output \
  --package-name vss_speed_interfaces \
  --mode leaf \
  --srv both --srv-use-msg \
  --timeseries both \
  --timeseries-delete \
  --topics Vehicle.Speed \
  --output-vspec ./out/transformed.vspec \
  --timestamp-struct-fqn VehicleDataTypes.Timestamp
```

## Usage

```bash
vspec export ros2interface \
  --vspec spec/VehicleSignalSpecification.vspec \
  -I spec \
  --types spec/MyTypes.vspec \
  --output ./out \
  --package-name vss_interfaces \
  --mode aggregate|leaf \
  [--srv get|set|both] \
  [--srv-use-msg | --no-srv-use-msg] \
  [--timeseries get|set|both] \
  [--timeseries-delete] \
  [--timestamp-struct-fqn <fqn>] \
  [--topics PATTERN ...] \
  [--exclude-topics PATTERN ...] \
  [--topics-file patterns.txt] \
  [--topics-case-insensitive] \
  [--output-vspec transformed.vspec]
```
