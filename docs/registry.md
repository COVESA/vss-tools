# Spec Registry

## Why this exists

When a VSS-based model grows and gets consumed by multiple tools, teams, and systems, a common problem emerges: how do you refer to a concept — a signal, a branch, a struct — in a way that is stable across time and across different modeling projects?

The fully qualified name (FQN) like `Vehicle.Cabin.Seat.Row1.DriverSide.Position` is human-readable and useful during development, but it is fragile as a long-term identifier. If a node gets renamed, restructured, or merged into another branch, any system that stored the FQN as a reference now has a broken link. There is no way to know that `Vehicle.Cabin.Seat.Row1.DriverSide.Position` and its successor `Vehicle.Cabin.Seat.Row1.Left.Position` refer to the same real-world concept.

The spec registry solves this by assigning a **stable, short numeric ID** to every node the first time it appears in the model. That ID never changes, even if the node is renamed or restructured. Systems downstream can store `covss:142` instead of the full FQN and always resolve it back to the current name via the registry.

This pattern is widely used in ontology engineering (RDF/OWL), standards bodies (ISO, W3C), and linked data systems. The registry tool brings the same discipline to VSS-based modeling projects.

---

## Important note: IDs are not deterministic

The IDs assigned by this tool depend on the **order in which nodes first appear** in the registry and the **current state of the modeling project at the time of the first sync**. Two projects that independently sync the same vspec will produce different numeric IDs for the same FQNs if they use different namespace prefixes or run the sync at different points in the model's history.

This is by design. Each project owns its own namespace and is responsible for when it first mints IDs. The IDs are only meaningful within a given namespace.

As a direct consequence, **the registry files must be treated as governed artifacts**:

- They should be committed to version control and never edited manually.
- Write access in CI should be restricted to tagged release pipelines only.
- The `vspec registry validate` command should run as a pre-commit hook and in every CI pipeline to catch any corruption early.

If the registry is corrupted or lost, previously published IDs cannot be reconstructed automatically. Treat the `registry.csv` file with the same care as a database migration history or a package lock file.

---

## Concepts

### Namespace

A namespace is a URI that scopes a set of IDs. Each project declares exactly one namespace it **owns** — the namespace under which it mints new IDs. It may also declare additional namespaces it **imports** — external namespaces it references but does not mint into.

### Prefix

A short label used as a human-readable abbreviation for a namespace URI. For example, `covss` is the prefix for `https://www.covesa.global/model/vss#`. IDs are written in CURIE form: `covss:42`.

### Composed ID

An ID in the form `<prefix>:<integer>`, for example `covss:0`, `covss:1`, `bmwvss:0`. The integer is assigned incrementally starting from 0, independently per prefix.

### Registry

A CSV file that acts as the append-only ledger mapping composed IDs to FQNs. Each row has a SHA-256 hash of its immutable fields, making manual edits detectable.

---

## File formats

### `namespaces.yaml`

Declares the namespace this project owns and any external namespaces it references.

```yaml
namespace:
  prefix: covss
  uri: "https://www.covesa.global/model/vss#"
  description: "COVESA Vehicle Signal Specification"  # optional

imports:                                               # optional
  myns:
    uri: "https://www.example.org/myModel#"
    description: "Private model extension"
```

Rules:
- `namespace` is required. It must have a `prefix` and a `uri`.
- `prefix` must match `^[a-z][a-z0-9]*$` — lowercase alphanumeric, no hyphens.
- `imports` is optional. A project cannot import its own prefix.
- All URIs should end with `#` or `/` so that composed IDs form valid full URIs when concatenated.

### `registry.csv`

The ledger file. Managed entirely by the tool — do not edit manually.

```
composed_id,fqn,int_id,status,row_hash
covss:0,Vehicle,0,active,e3b0c44298fc1c149afb...
covss:1,Vehicle.Cabin,1,active,a87ff679a2f3e71d9181...
covss:2,Vehicle.Cabin.Seat,2,active,1679091c5a880faf6fb...
```

Column meanings:
- `composed_id` — the stable identifier, e.g. `covss:0`
- `fqn` — the fully qualified node name at the time the ID was minted
- `int_id` — the numeric part of `composed_id`, per-prefix counter
- `status` — `active` or `deprecated`. If a concept is not present in a future release of the model, then it is because it was deleted from the model. However, the id is persisted forever in the registry.
- `row_hash` — SHA-256 of `"{composed_id}|{fqn}"`, used to detect tampering

---

## Commands

### `vspec registry sync`

Reads the current vspec model, finds any FQNs not yet in the registry, and mints new IDs for them. Safe to run repeatedly — existing rows are never modified.

```bash
vspec registry sync \
  -s spec.vspec \
  -u units.yaml \
  -q quantities.yaml \
  -n namespaces.yaml \
  -r registry.csv
```

With include directories and type files (for models split across multiple files):

```bash
vspec registry sync \
  -s spec.vspec \
  -I includes/ \
  -t types.vspec \
  -u units.yaml \
  -q quantities.yaml \
  -n namespaces.yaml \
  -r registry.csv
```

With optional JSON-LD sidecar export:

```bash
vspec registry sync \
  -s spec.vspec \
  -u units.yaml \
  -q quantities.yaml \
  -n namespaces.yaml \
  -r registry.csv \
  --export-jsonld registry.jsonld
```

The JSON-LD sidecar is a derived artifact — it is regenerated from the CSV on every run and is safe to discard and regenerate at any time.

### `vspec registry validate`

Checks both files for integrity without writing anything. Exits with a non-zero status code if any check fails. Suitable for use as a pre-commit hook or CI step.

```bash
vspec registry validate \
  -n namespaces.yaml \
  -r registry.csv
```

---

## Scenario: COVESA mints the base VSS model

A COVESA project maintains the canonical VSS model. On every release they sync the registry to assign stable IDs to all nodes:

**`namespaces.yaml`** (COVESA project):
```yaml
namespace:
  prefix: covss
  uri: "https://www.covesa.global/model/vss#"
  description: "COVESA Vehicle Signal Specification"
```

```bash
vspec registry sync \
  -s Vehicle.vspec \
  -u units.yaml \
  -q quantities.yaml \
  -n namespaces.yaml \
  -r registry.csv
```

After the first sync, `registry.csv` contains one row per VSS node:

```
composed_id,fqn,int_id,status,row_hash
covss:0,Vehicle,0,active,e3b0c44298fc...
covss:1,Vehicle.ADAS,1,active,a87ff679a2...
covss:2,Vehicle.Cabin,2,active,1679091c5a...
...
```

This file is committed to the COVESA repo and published alongside the vspec release.

---

## Scenario: A private project extends the model using an overlay

A private modeling project builds on top of the COVESA VSS model by overlaying additional signals. They want to:
1. Reuse the stable COVESA IDs for all COVESA nodes.
2. Mint their own IDs under a different prefix for project-specific nodes.

**Step 1**: The project copies the COVESA `registry.csv` as its starting point. This file already contains all the `covss:N` rows.

**Step 2**: The project creates its own `namespaces.yaml`:

```yaml
namespace:
  prefix: myns
  uri: "https://www.example.org/myModel#"
  description: "Private VSS extension"

imports:
  covss:
    uri: "https://www.covesa.global/model/vss#"
    description: "COVESA VSS — imported reference"
```

**Step 3**: They run sync with their overlay applied:

```bash
vspec registry sync \
  -s Vehicle.vspec \
  -l my_extension.vspec \
  -u units.yaml \
  -q quantities.yaml \
  -n namespaces.yaml \
  -r registry.csv
```

Because all COVESA FQNs are already in the registry (with `covss:N` IDs), the tool only mints IDs for nodes that are genuinely new — those introduced by the private overlay:

```
composed_id,fqn,int_id,status,row_hash
covss:0,Vehicle,0,active,e3b0c44298fc...
covss:1,Vehicle.ADAS,1,active,a87ff679a2...
...
myns:0,Vehicle.MyProject.FeatureA,0,active,7f8f4af0c8...
myns:1,Vehicle.MyProject.FeatureA.Status,1,active,9bf31c7ff0...
```

The result is a single registry file that:
- Preserves all COVESA stable IDs unchanged.
- Adds project-specific IDs starting from `myns:0`.
- Makes it unambiguous which concepts belong to which namespace at a glance.

The optional JSON-LD sidecar makes both namespaces resolvable to full URIs for any toolchain that consumes linked data:

```json
{
  "@context": {
    "covss": "https://www.covesa.global/model/vss#",
    "myns": "https://www.example.org/myModel#"
  },
  "@graph": [
    {"@id": "covss:0", "fqn": "Vehicle", "status": "active"},
    {"@id": "covss:1", "fqn": "Vehicle.ADAS", "status": "active"},
    {"@id": "myns:0", "fqn": "Vehicle.MyProject.FeatureA", "status": "active"},
    {"@id": "myns:1", "fqn": "Vehicle.MyProject.FeatureA.Status", "status": "active"}
  ]
}
```
