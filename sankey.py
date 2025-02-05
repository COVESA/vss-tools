import pandas as pd

# vspec export csv -s VehicleSignalSpecification.vspec -o VSS_TableData.csv --no-expand    

data_metadata = pd.read_csv('VSS_TableData.csv')
data_metadata = data_metadata[~data_metadata.isin(['branch']).any(axis=1)]

column_names = data_metadata.columns.tolist()
print(column_names)

data_metadata['Property'] = data_metadata['Type'].apply(
    lambda x: "dynamic" if x in ["sensor", "actuator"] else "static"
)
columns_to_drop = ['Signal', 'Desc', 'Deprecated', 
                   'Unit', 'Min', 'Max', 'Allowed','Comment',
                   'Default', 'Instances']
data_metadata.drop(columns=columns_to_drop, inplace=True)
data_metadata['Dummy'] = 0

def print_unique_values(data):
    for column in data.columns:
        unique_values = data[column].unique()
        print(f"Unique values in column '{column}':")
        print(unique_values)
        print("-" * 50)

columns_order = [ 'Property', 'Type', 'DataType', 'Dummy']
data_metadata = data_metadata[columns_order]

print_unique_values(data_metadata)

data_metadata.to_csv('sankey.csv', index=False)
