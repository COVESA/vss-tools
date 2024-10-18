# ID - vspec static UID generator and validator

The `id` exporter is used to generate and validate static UIDs for all
nodes in the tree. These static UIDs serve as unique identifiers for
transmitting data between nodes. They are designed to replace long strings like
`Vehicle.Body.Lights.DirectionIndicator.Right.IsSignaling` with compact 4-byte
identifiers.

## General usage

```bash
 Usage: vspec export id [OPTIONS]

 Export as IDs.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --vspec                -s  FILE                            The vspec file. [required]                   │
│ *  --output               -o  FILE                            Output file. [required]                      │
│    --include-dirs         -I  DIRECTORY                       Add include directory to search for included │
│                                                               vspec files.                                 │
│    --extended-attributes  -e  TEXT                            Whitelisted extended attributes, comma       │
│                                                               separated.                                   │
│    --strict/--no-strict                                       Whether to enable strict. Enables all        │
│                                                               '--abort/-a' values.                         │
│                                                               [default: no-strict]                         │
│    --aborts               -a  [unknown-attribute|name-style]  Abort on selected option. The '--strict'     │
│                                                               option enables all of them.                  │
│    --expand/--no-expand                                       Whether to expand the tree.                  │
│                                                               [default: expand]                            │
│    --overlays             -l  FILE                            Overlay files to apply on top of the vspec.  │
│    --quantities           -q  FILE                            Quantity files. [default:                    │
│                                                               VSPEC/quantities.yaml]                       │
│    --units                -u  FILE                            Unit files. [default: VSPEC/units.yaml]      │
│    --types                -t  FILE                            Data types files.                            │
│    --types-output             FILE                            Output file for writing data types from      │
│                                                               vspec file. If not specified, a single file  │
│                                                               is used where applicable. In case of JSON    │
│                                                               and YAML, the data is exported under a       │
│                                                               special key: "ComplexDataTypes",             │
│    --validate-static-uid      FILE                            Validation file.                             │
│    --validate-only                                            Only validating. Not exporting.              │
│    --case-sensitive                                           Whether the generation of static UIDs is     │
│                                                               case-sensitive                               │
│    --help                                                     Show this message and exit.                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Example

To initially run this you will need a vehicle signal specification, e.g.
[COVESA Vehicle Signal Specification](https://github.com/COVESA/vehicle_signal_specification).
If you are just starting to use static UIDs the first run is simple. You will
only use the static UID generator by running the command below. Please note that
if you want to use any overlays, now is the time to do so:

```bash
cd path/to/your/vss
vspec export id --vspec spec/VehicleSignalSpecification.vspec --output output_id_v1.vspec
# or if you are using an overlay e.g. called overlay.vspec
vspec export id --vspec spec/VehicleSignalSpecification.vspec --output output_id_v1.vspec -l overlay.vspec
```

Great, you generated your first vspec including static IDs that will also be
used as your validation file as soon as you update your vehicle signal
specification or your overlay.

If needed you can make the static UID generation case-sensitive using the
command line argument `--strict`. It will default to false.

### Generate e.g. yaml file with static UIDs

Now if you just want to generate a new e.g. yaml file including your static
UIDs, please use the corresponding exporter (here we will use
`yaml`). Please note that if you are outside of the spec folder in
the vehicle specification you will have to specify the path to the units.yaml
using `-u`.

```bash
cd path/to/your/vss
vspec export yaml --vspec output_id_v1.vspec --output vehicle_specification_with_uids.yaml -e staticUID -u spec/units.yaml
```

### Using constant UIDs for specific attributes

In case you want to use a specific predefined 4-byte hex ID for an attribute in
your tree, you can define a `constUID` in your overlay which will be used
instead of the generated static UID. Let's say you want to use a constant ID
`0x00112233` for the signal if the driver is wearing a seatbelt which looks like
this

```yaml
Seat:
  type: branch
  instances:
    - Row[1,2]
    - ["DriverSide","Middle","PassengerSide"]
  description: All seats.
#include SingleSeat.vspec Seat

```

In the overlay define the one you would like to give a constant ID to and define
a new attribute called `constUID`:

```yaml
Vehicle.Cabin.Seat.Row1.DriverSide.IsBelted:
  datatype: boolean
  constUID: '0x00112233'
  type: sensor
```

Let's say the snippet above is a file called `const_id_overlay.vspec`, you could
run the vspec id exporter like this:

```bash
vspec export id --vspec spec/VehicleSignalSpecification.vspec --output const_test.vspec -l const_overlay.vspec
```

which will give you the following `INFO` msg and write the defined constant ID
as the static ID in your generated vspec.

```bash
...
INFO     Calling exporter...
INFO     Generating YAML output...
INFO     Using const ID for Vehicle.Cabin.Seat.Row1.DriverSide.IsBelted. If you didn't mean to do that you can remove it in your vspec / overlay.
INFO     All done.
```

This works for all types of signal even enums (as shown above). Please note that
if you use a constant UID, you will not be able to do proper validation on the
signal. Validation will be further explained in the next section.

### Validation

In this case you want to validate changes of your vehicle specification. If you
are doing a dry run try temporarily renaming a node or changing the node's
datatype, unit, description, or other. You will get warnings depending on your
changes in the vehicle signal specification.

The validation step compares your current changes of the vehicle signal
specification to a previously generated file, here we named it
`output_id_v1.vspec`. There are two types of changes `BREAKING CHANGES` and
`NON-BREAKING CHANGES`. A `BREAKING CHANGE` will generate a new hash for a node.
A `NON-BREAKING CHANGE` will throw a warning, but the static ID will remain the
same. A `BREAKING CHANGE` is triggered when you change name/path, unit, type,
datatype, enum values (allowed), or minimum/maximum. These attributes are part
of the hash so they a `BREAKING CHANGE` automatically generates a new hash for a
static UID. In case you want to keep the same ID but rename a node, this we call
a `SEMANTIC CHANGE`, you can add an attribute called `fka` in the vspec (which
is a list of strings) and add a list of names to it as shown below for
`A.B.NewName`. The same holds for path changes, if you move a node between
layers you can add the `fka` attribute containing the full path as shown below.

Before renaming `A.B.NewName` its name was `A.B.OldName`.

```yaml
A.B.NewName:
  datatype: string
  type: actuator
  allowed: ["YES", "NO"]
  description: A.B.NewName's old name is 'OldName'. And its even older name is 'OlderName'.
  fka: ['A.B.OlderName', 'A.B.OldName']
```

or

```yaml
A.B.NewName:
  datatype: string
  type: actuator
  allowed: ["YES", "NO"]
  description: A.B.NewName's old name is 'OldName'. And its even older name is 'OlderName'.
  fka: A.B.OlderName
```

In order to add fka attribute, one can add fka directly into the vspec file or
use overlay feature of vss-tools.

Example mycustom-overlay-fka.vspec

```yaml
A.B.NewName:
  datatype: string
  type: actuator
  fka: A.B.OlderName
```

As stated if you want to rename the node `A.B.NewName` to `A.NewName` you can
also write the Formerly Known As `fka` attribute stating its legacy path. For
hashing function in previous case `A.B.OlderName` will be used.

To summarize these are the `BREAKING CHANGES` that affect the hash and
`NON-BREAKING CHANGES` that throw warnings only:

| BREAKING CHANGES      |     | NON-BREAKING CHANGES |
|-----------------------|-----|----------------------|
| Qualified name        |     | Added attribute      |
| Data type             |     | Deprecation          |
| Type (i.e. node type) |     | Deleted Attribute    |
| Unit                  |     | Change description   |
| Enum values (allowed) |     | Qualified name (fka) |
| Minimum               |     |                      |
| Maximum               |     |                      |

Now you should know about all possible changes. To run the validation step,
please do:

```bash
vspec export id --vspec spec/VehicleSignalSpecification.vspec --output output_id_v2.vspec --validate-static-uid output_id_v1.vspec
```

Depending on what you changed in the vehicle signal specification the
corresponding errors will be triggered.

Now, if the warning logs correspond to what you have changed since the last
validation, you can continue to generate e.g. a yaml file with your validated
changes as described in the `Generate e.g. yaml file with static UIDs` step
above.

### Collision of hashed values

In case of collision of hashed values we currently perform a system exit, the probability of a hash collision
using the [Birthday Problem approximation](https://ekamperi.github.io/mathematics/2019/11/09/birthday-paradox-factorial-approximations-laplace-method.html) is currently `0.0197%` for the (as of now) about 1300
signals in the base specification.

$$
P(collision) \approx 1 - e^{-\frac{k^2}{2n}}
$$

where

* $k$ is number of signals in your specification and
* $n$ is the number of possible hash values (here $2^{32}$ values).

However, if you run into a hash collision, you can use constant UID attribute described above to prevent the system exit and generate your vspec with IDs.

### Tests

If you want to run the tests for the vspec id exporter implementation, please do

```bash
cd path/to/vss-tools
pytest tests/vspec/test_static_uids
```

Depending on how you are using the implementation you might have to activate
your virtual environment as described on the top README.
