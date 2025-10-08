
# Vspec ROS Exporter

Exports a VSS model to a ROS 2 interface package.

## What this exporter is about?
This exporter takes VSS `Vspec` file as a source and it generates `.msg` files (per leaf or aggregated by parent branch) and optional `.srv` files for Get/Set operations. This exporter plugs into the `vspec export` CLI like other vss-tools exporters. For generic exporter usage and common arguments, see the `vspec` documentation.

## Generated Output Structure
```
\<output><br>
└── \<package-name><br>
    ├── msg  # generated .msg definitions<br>
            │ &emsp; └── \<MSG>.msg<br>
            └── srv  # generated .srv (if setting is enabled)<br>
                        ├── Get\<MSG>.srv<br>
                        └── Set\<MSG>.srv<br>
```

- .msg files include VSS metadata as comments (description, unit, min/max, allowed values).
- Optional .srv files (Get\<Msg>.srv, Set\<Msg>.srv) that either nest the generated message or flatten its fields.


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
- `--package-name <name>`: Name of generated ROS 2 interface package (default: `vss_interfaces`).
- `--mode {aggregate, leaf}`:
  - `aggregate`: one `.msg` per direct parent branch containing all of its leaf signals.
  - `leaf`: one `.msg` per leaf signal.
- `--srv {none, get, set, both}`: Also generate `.srv` files.
  - `none`:
    - using this option does not create any .srv files
  - `get`:
    - creates Get<MSG>.srv files to retrieve data within a specified start and end time.
  - `set`:
    - creates Set<MSG>.srv files to send the data and get true as response if the data gets saved.
  - `both`:
    - creates both the Get<MSG>.srv and Set<MSG>.srv files
- `--srv-use-msg / --no-srv-use-msg`: In services, use the generated message as a nested field (default: `--srv-use-msg`); otherwise flatten fields.

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

### Messages (`.msg`)

- `Aggregate` mode
  one message per direct parent branch. Fields include a leading `uint64 timestamp`, then one field per child leaf.

- `Leaf` mode
  one message per leaf. Fields include `uint64 timestamp` and one field for the leaf value.

### Services (`.srv`)

This file is Generated when `--srv none|get|set|both` parameter is used. The output files are:

- `Get<Msg>.srv`
  - Request: `uint64 start_time_ms`, `uint64 end_time_ms`
  - Response: `Msg[] data` or flattened fields

- `Set<Msg>.srv`
  - Request: `Msg data` or flattened fields
  - Response: `bool success`, `string message`

## Examples

```bash
# Export only Vehicle.Speed as leaf message + get/set services:
vspec export ros2interface   --vspec spec/VehicleSignalSpecification.vspec   -I spec   --output ./out   --package-name vss_speed_interfaces   --mode leaf   --srv both --srv-use-msg   --topics Vehicle.Speed

# Export all *.Speed signals, aggregated by their parent branches:
vspec export ros2interface   --vspec spec/VehicleSignalSpecification.vspec   -I spec   --output ./out   --package-name vss_speed_agg   --mode aggregate   --srv get   --topics '*.Speed'
```
## Usage

```bash
vspec export ros2interface   --vspec spec/VehicleSignalSpecification.vspec   -I spec   --output ./out   --package-name vss_interfaces   --mode aggregate|leaf   --srv none|get|set|both   [--srv-use-msg | --no-srv-use-msg]   [--topics PATTERN ...]   [--exclude-topics PATTERN ...]   [--topics-file patterns.txt]   [--topics-case-insensitive]
```
