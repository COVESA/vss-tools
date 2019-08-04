---
title: "Data Entry"
date: 2019-08-04T11:11:30+02:00
draft: true
chapter: true
weight: 2
---

# Data Entry
Leaf nodes of the tree contain metadata describing the data associated to the node.
This specification makes a distinction between signals - in the following as ```sensor```, ```actuator``` and ```stream``` - and ```attributes```.
The difference between a signal and an attribute is that the signal has
a publisher (or producer) that continuously updates the signal value while an
attribute has a set value, defined in the specification, that never changes.
As summary, besides [```branch```](/rule_set/branches) and ```rbranch``` type can be:

* **```attribute```**, which describes static read-only value.
* **```sensor```**, which describes non-static read-only signal.
* **```actuator```**, same as sensor plus the possibility of changing the value.
* **```stream```**, data stream like video.
