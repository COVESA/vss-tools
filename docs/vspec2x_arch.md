# vspec2x Design Decisions, Architecture and Limitations

## Overlays

Each overlay is treated as a separate tree and merged (after expansion) on the existing tree.
This means that descriptions, comments, datatype, unit and similar attributes gets overwritten if existing.

## Expansion

Expansion is the process where a branch with instances is replaced with multiple branches.

This will result in that e.g. `Vehicle.Cabin.Door` is expanded to the following branches

* `Vehicle.Cabin.Door.Row1.Left`
* `Vehicle.Cabin.Door.Row1.Right`
* `Vehicle.Cabin.Door.Row2.Left`
* `Vehicle.Cabin.Door.Row2.Right`

For some exporters expansion can be suppressed by using the `--no_expand` option.
Then instance information will be represented by other means in the resulting output.

## Deletion / Node removal

Nodes can be removed from the tree by using the `delete` element in the overlay.
This is useful when a signal is not used in a next version of the specification or if you
simply want to delete a node or branch from the specification, e.g. you are not using a signal of the base
specification.
Please note, that the deletion for branches will delete all nodes that are connected to that branch (which is
desired behavior). Also, if a branch node is deleted, all nodes that are connected to that branch will be deleted
irrespective of what their delete element value is.

We chose three examples to show what you can do with the delete element. Let's say we have the following excerpt from
the base vehicle signal specification:

```yaml
Vehicle.Service:
  description: Service data.
  type: branch

Vehicle.Service.DistanceToService:
  datatype: float
  description: Remaining distance to service (of any kind). Negative values indicate service overdue.
  type: sensor
  unit: km

Vehicle.Service.IsServiceDue:
  datatype: boolean
  description: Indicates if vehicle needs service (of any kind). True = Service needed now or in the near future. False = No known need for service.
  type: sensor

Vehicle.Service.TimeToService:
  datatype: int32
  description: Remaining time to service (of any kind). Negative values indicate service overdue.
  type: sensor
  unit: s
```

Now if you want to delete the `Vehicle.Service.TimeToService` node from the specification, you can do this by adding the
delete element to your overlay like this:

```yaml
Vehicle.Service.TimeToService:
  type: sensor
  datatype: int32
  delete: true
```

Let's say you now want to delete the whole branch `Vehicle.Service` from the specification. You can do this by adding:

```yaml
Vehicle.Service:
  type: branch
  delete: true
```

Also, the delement element can be used on instances after they have been expanded. If you want to delete a node or
branch that has been expanded using instances you can add the `delete` element to the overlay, let's say the vehicle
only has two doors in the front. In this case we would like to delete the signals for the rear doors:

```yaml
Vehicle.Cabin.Door.Row2:
  type: branch
  delete: true
```

By adding the `delete: true` to a node or branch all nodes and branches connected to it are deleted by vss-tools
when converting to a different format.

Please note that for branches you need to provide at least the `type` element to
the overlay. For nodes you at least have to provide the `type` and `datatype` elements. Currently, the elements provided
do not have to match the previously given elements in the base specification.

## Expansion and Overlays

Sometimes an overlay only refers to a signal in a specific branch, like:

```yaml
Vehicle.Cabin.Door.Row2.Right.NewSignal:
  datatype: int8
  type: sensor
  unit: km
  description: A new signal for just one door.
```

We do not want this signal expanded, and the tooling prevents expansion by taking the instance `Row2` and comparing with
instances declared for `Door`.

```yaml
Door:
  type: branch
  instances:
    - Row[1,2]
    - [ "Left","Right" ]
  description: d1
  comment: c1
```

It will do this by taking the instances on first level (`Row1` and `Row2`) and if comparing with current
branch (`Row2`).
If they match it will repeat the check for `Right`and finally merge `NewSignal` with other signals
in `Vehicle.Cabin.Door`.

Description, comments and other data defined for a specific instance (like `Vehicle.Cabin.Door.Row2.Right.NewSignal`
above) have precedence
over data defined for the unexpanded signal `Vehicle.Cabin.Door.NewSignal`.

The merge algorithm tries to be smart, so that if you use `Row*` it assume it is an instantiated branch if branch has an
instance declaration of type `Row[m,n]`,
even if the the value of `Row*` is outside the range. It will however in that case not inherit values from the base
branch.

## Linters and Static Code Checkers

### MyPy

[Mypy](https://mypy-lang.org/) is used for static type checking of code.
General ambition is to resolve errors reported by mypy, but when not feasible errors are suppressed
by using `# type: ignore[<type>]` as comment on the concerned line.
Continuous Integration requires that no Mypy errors are reported.

To run manually:

```bash
mypy src tests contrib
```

Suppressed error categories include:

* Template types in `constants.py` have expectations on subclasses that may not be fulfilled in the general case,
  but are fulfilled in our cases.
* Some dependencies like `anytree` and `deprecation` does not have library stubs or `py.typed`
  and can thus not be analyzed.
* Mypy does not like "method variables" like `load_flat_model.include_index`

### Flake8

Flake8 is used as linter. It is also configured to be used as pre-commit hook.
The Continuous Integration currently accepts errors reported by Flake8,
this might change in the future.
New or changed code shall not produce any Flake8 issues.

The project use the following deviations compared to default settings:

* Max line length is 120

To enable the hook to check when creating a commit:

```bash
pre-commit install
```

To run manually:

```bash
flake8 src tests contrib
```
