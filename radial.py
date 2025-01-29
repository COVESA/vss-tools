import json
# vspec export json -s VehicleSignalSpecification.vspec -o Data.json  
# Load the input JSON data
with open('Data.json', 'r') as file:
    data = json.load(file)

# Define a function to recursively build the new JSON structure
def build_json_structure(obj, parent_name=None):
    result = []
    for key, value in obj.items():
        item = {'name': key}
        if 'children' in value:
            item['children'] = build_json_structure(value['children'], key)
        else:
            for prop, prop_value in value.items():
                if prop != 'children':
                    item[prop] = prop_value
        result.append(item)
    
    # Sort nodes with children to the top
    result.sort(key=lambda x: (not ('children' in x), x.get('type', '')))
    return result

# Build the new JSON structure
new_data = {
    'name': 'Vehicle',
    'type': 'Vehicle',
    'children': build_json_structure(data['Vehicle']['children'])
}

# Save the new JSON data to a file
with open('radial.json', 'w') as file:
    json.dump(new_data, file, indent=2)