# AVRO Exporter

This exporter converts VSS struct definitions into [Apache Avro IDL (`.avdl`)](https://avro.apache.org/docs/current/idl-language/) files, one file per top-level struct. The output is ready to be compiled into `.avsc` schemas and used with [Avro single-object encoding](https://avro.apache.org/docs/current/specification/#single-object-encoding) for efficient binary serialization over the wire.

## What it does

For every top-level `struct` found in the `--types` files, the exporter writes one `.avdl` file into the output directory. Each file defines a self-contained Avro protocol that includes:

- All **enum types** required by the struct (one per field with `allowed` values).
- All **nested record types** defined inside the struct.
- The **main record** for the struct itself.
- An optional **array container record** (enabled with `--include-array-record`).

Only top-level structs produce output files. Nested structs (structs defined inside another struct) are included as records inside their parent's file, not as separate files.

## Usage

```bash
vspec export avro \
  -s <signals.vspec> \
  -t <types.vspec> \
  -o <output-dir> \
  --namespace <avro.namespace.prefix>
```

The main signals file (`-s`) is required by the VSS toolchain but is not exported — only the struct definitions provided via `--types` (`-t`) are processed.

### Options

| Option | Required | Description |
|---|---|---|
| `-s` / `--vspec` | yes | Main VSS signals file (not exported, just parsed). |
| `-t` / `--types` | yes | One or more VSS files containing struct definitions. |
| `-o` / `--output` | yes | Output directory. Created automatically if it does not exist. |
| `--namespace` | yes | Avro namespace prefix (e.g. `com.example.vss.struct`). |
| `--file-prefix` | no | String prepended to each output filename (e.g. `struct` → `structColor.avdl`). Default: empty. |
| `--include-array-record` | no | Also generate an array container record for each struct. Default: off. |
| `-u` / `--units` | no | Unit definition files. Required only when the vspec uses `unit:` fields. |
| `-q` / `--quantities` | no | Quantity definition files. Required only when the vspec uses `unit:` fields. |
| `-l` / `--overlays` | no | Overlay files applied on top of the vspec. |
| `-I` / `--include-dirs` | no | Additional directories to search for included vspec files. |

## Type mapping

VSS datatypes map to Avro types as follows:

| VSS | Avro |
|---|---|
| `uint8`, `int8`, `uint16`, `int16`, `int32` | `int` |
| `uint32`, `int64`, `uint64` | `long` |
| `float` | `float` |
| `double` | `double` |
| `boolean` | `boolean` |
| `string` (no `allowed`) | `string` |
| `string` (with `allowed`) | enum type (see [Enums](#enums)) |
| any array type (`T[]`) | `bytes` |
| nested struct field | record reference by short name |

Every field is wrapped in `union { null, T }`, making all fields nullable by default. This is intentional and aligns with Avro community conventions for optional fields.

## Enums

When a property has an `allowed` list, the exporter creates a dedicated Avro enum for that field. Enums are never shared between fields — each field gets its own type, even if the allowed values are identical. This maintains a one-to-one mapping between vspec field definitions and Avro enum types.

**Naming pattern:** `{StructPath}{FieldName}Value`

The path is built from all struct names from the top-level struct down to the containing struct. Examples:

| vspec path | Avro enum name |
|---|---|
| `Types.LogEntry.Level` | `LogEntryLevelValue` |
| `Types.DataPacket.Header.Status` | `DataPacketHeaderStatusValue` |

**`UNKNOWN` is always the first value** (position 0) and is used as the default. This ensures forward compatibility — decoders that receive an unrecognised value fall back gracefully. If `UNKNOWN` is already present in the vspec `allowed` list it is kept in position 0 without being duplicated.

```avro
enum LogEntryLevelValue {
    UNKNOWN,
    DEBUG,
    INFO,
    WARNING,
    ERROR
} = UNKNOWN;
```

## Nested structs

Structs defined inside another struct become records within the same protocol file. They are declared in post-order (deepest nested first) so that every type is defined before it is referenced.

The nested record uses only its own short name (last path segment), not the fully-qualified path. Because each top-level struct lives in its own file and namespace, short names are unambiguous.

## Array container record

When `--include-array-record` is set, the exporter appends a second record that wraps an array of the main struct. This is useful when a VSS signal uses an array of the struct type (e.g. `datatype: MyTypes.Color[]`) and the consumer needs a distinct Avro schema with its own fingerprint for single-object encoding.

The array field name is the **plural form** of the struct name in lowerCamelCase, computed automatically (e.g. `Color` → `colors`, `LogEntry` → `logEntries`, `DataPacket` → `dataPackets`).

```avro
record ColorArray {
    array<Color> colors;
}
```

## Declaration order within a protocol

Each generated protocol follows this fixed order:

1. Enums (depth-first across all nested levels)
2. Nested records (deepest first)
3. Main record
4. Array container record (if requested)

## Example

Given the following VSS type definition:

```yaml
MyTypes:
  type: branch
  description: Test types.

MyTypes.LogEntry:
  type: struct
  description: A log entry.

MyTypes.LogEntry.Level:
  type: property
  datatype: string
  allowed: ["DEBUG", "INFO", "WARNING", "ERROR"]
  description: Severity level.

MyTypes.LogEntry.Message:
  type: property
  datatype: string
  description: Log message text.

MyTypes.LogEntry.SequenceNumber:
  type: property
  datatype: uint32
  description: Ordering counter.
```

Running:

```bash
vspec export avro \
  -s signals.vspec \
  -t types.vspec \
  -o ./out \
  --namespace com.example.struct \
  --file-prefix struct \
  --include-array-record
```

Produces `out/structLogEntry.avdl`:

```avro
@namespace("com.example.struct.logentry")
protocol LogEntry {

    enum LogEntryLevelValue {
        UNKNOWN,
        DEBUG,
        INFO,
        WARNING,
        ERROR
    } = UNKNOWN;

    record LogEntry {
        union { null, LogEntryLevelValue } level;
        union { null, string } message;
        union { null, long } sequenceNumber;
    }

    record LogEntryArray {
        array<LogEntry> logEntries;
    }
}
```

## Namespace

The full Avro namespace for each struct is `<--namespace>.<structnamelowercase>`. For example, with `--namespace com.example.struct` and a struct named `DataPacket`, the namespace becomes `com.example.struct.datapacket`.
