from __future__ import annotations
import yaml

def load_tree(filepath):
    with open(filepath, "r") as f:
        tree = yaml.load(f.read(), Loader=yaml.SafeLoader)
    return tree
