import pandas as pd
from collections import Counter

# The actual data for fallbacks
template_data = {
    'Type': ['Attribute', 'Branches', 'Sensors', 'Actuators'],
    'V2': [78, 117, 203, 101],
    'V3': [86, 117, 263, 128],
    'V4': [97, 147, 286, 179],
    'V5': [110, 131, 313, 195]
}

# vspec export csv -s VehicleSignalSpecification.vspec -o VSS_TableData.csv --no-expand    

# Load the output DataFrame from the piechart.csv file
output = pd.read_csv('piechartversions.csv')

# Load the metadata
metadata = pd.read_csv('vss-6-metadata.csv')

# Convert the 'default' column to integers
metadata['Default'] = pd.to_numeric(metadata['Default'], errors='coerce')

# Extract the major version number
major_version = None
for index, row in metadata.iterrows():
    if 'Vehicle.VersionVSS.Major' in row['Signal'] and row['Default'] > 5:
        major_version = int(row['Default'])
        break

# Check the conditions and count the types
if (major_version is not None):
    
    # Count the types
    type_counts = Counter(metadata['Type'])
    counts = {
        'Branches': type_counts.get('branch', 0),
        'Sensors': type_counts.get('sensor', 0),
        'Actuators': type_counts.get('actuator', 0),
        'Attributes': type_counts.get('attribute', 0),
    }
    
    # Add a new column if it does not already exist
    column_name = f'V{major_version}'
    if column_name not in output.columns:
        output[column_name] = pd.Series([counts['Attributes'], counts['Branches'], counts['Sensors'], counts['Actuators']])

# Save the updated DataFrame back to piechart.csv
output.to_csv('piechartversions.csv', index=False)

print(output)

