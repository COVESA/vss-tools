from __future__ import annotations
import yaml

def load_tree(filepath):
    with open(filepath, "r") as f:
        tree = yaml.load(f.read(), Loader=yaml.SafeLoader)
        # Create input items for the complex yaml formulas
        translator=str.maketrans({"/":" ","*":" ","+":" ","(":" ",")":" ","!":" ","&":" ","%":" ","^":" ","|":" ","\t":" "})
        for key,item in tree.items():
            if "translation" in item:
                if "complex" in item["translation"]:
                    formula_elements=item["translation"]["complex"].translate(translator).split()
                    item["translation"]["input"]=[element[1:] for element in formula_elements if element[0]=="$"]
    return tree
