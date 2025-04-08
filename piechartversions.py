from collections import Counter

import pandas as pd

# vspec export csv -s VehicleSignalSpecification.vspec -o VSS_TableData.csv --no-expand

# The actual data of first 5 version for fallbacks
# template_data = {
#     'Type': ['Attribute', 'Branches', 'Sensors', 'Actuators'],
#     'V2': [78, 117, 203, 101],
#     'V3': [86, 117, 263, 128],
#     'V4': [97, 147, 286, 179],
#     'V5': [110, 131, 313, 195]
# }

latest = pd.read_csv("piechartversions.csv")
metadata = pd.read_csv("VSS_TableData.csv")

metadata["Default"] = pd.to_numeric(metadata["Default"], errors="coerce")

major_version = None
for index, row in metadata.iterrows():
    if "Vehicle.VersionVSS.Major" in row["Signal"] and row["Default"] > 5:
        major_version = int(row["Default"])
        break

if major_version is not None:
    type_counts = Counter(metadata["Type"])
    counts = {
        "Branches": type_counts.get("branch", 0),
        "Sensors": type_counts.get("sensor", 0),
        "Actuators": type_counts.get("actuator", 0),
        "Attributes": type_counts.get("attribute", 0),
    }

    column_name = f"V{major_version}"
    if column_name not in latest.columns:
        latest[column_name] = pd.Series(
            [counts["Attributes"], counts["Branches"], counts["Sensors"], counts["Actuators"]]
        )

latest.to_csv("piechartversions.csv", index=False)

print(latest)
