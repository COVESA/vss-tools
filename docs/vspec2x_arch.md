# vspec2x Design Decisions, Architecture and limitations



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

## Expansion and Overlays

Sometimes an overlay only refers to a signal in a specific branch, like:

```
Vehicle.Cabin.Door.Row2.Right.NewSignal:
  datatype: int8
  type: sensor
  unit: km
  description: A new signal for just one door.
```

We do not want this signal expanded, and the tooling prevents expansion by taking the instance `Row2` and comparing with instances declared for `Door`.

```
Door:
  type: branch
  instances:
    - Row[1,2]
    - ["Left","Right"]
  description: d1
  comment: c1
```

It will do this by taking the instances on first level (`Row1` and `Row2`) and if comparing with current branch (`Row2`).
If they match it will repeat the check for `Right`and finally merge `NewSignal` with other signals in `Vehicle.Cabin.Door`.

Description, comments and other data defined for a specific instance (like `Vehicle.Cabin.Door.Row2.Right.NewSignal` above) have precedence
over data defined for the unexpanded signal `Vehicle.Cabin.Door.NewSignal`.

The merge algorithm tries to be smart, so that if you use `Row*` it assume it is an instantiated branch if branch has an instance declaration of type `Row[m,n]`,
even if the the value of `Row*` is outside the range. It will however in that case not inherit values from the base branch.
