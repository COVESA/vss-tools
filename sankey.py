import pandas as pd

# vspec export csv -s VehicleSignalSpecification.vspec -o VSS_TableData.csv --no-expand    
# Load the data into a DataFrame
data_metadata = pd.read_csv('vss-6-metadata.csv')

# Filter out rows containing 'branch'
data_metadata = data_metadata[~data_metadata.isin(['branch']).any(axis=1)]

# Get the list of remaining column names
column_names = data_metadata.columns.tolist()
print(column_names)

# Extract the substring between the first and second delimiter "."
data_metadata['Property'] = data_metadata['Type'].apply(
    lambda x: "dynamic" if x in ["sensor", "actuator"] else "static"
)



# Define the column names to be dropped
columns_to_drop = ['Signal', 'Desc', 'Deprecated', 
                   'Unit', 'Min', 'Max', 'Allowed','Comment',
                   'Default', 'Instances']
data_metadata.drop(columns=columns_to_drop, inplace=True)
data_metadata['Dummy'] = 0


# Function to print unique values in each column
def print_unique_values(data):
    for column in data.columns:
        unique_values = data[column].unique()
        print(f"Unique values in column '{column}':")
        print(unique_values)
        print("-" * 50)

# Rearrange columns by specifying the correct order
columns_order = [ 'Property', 'Type', 'DataType', 'Dummy']
data_metadata = data_metadata[columns_order]

# Call the function
print_unique_values(data_metadata)

# Save the modified data into a new CSV file
data_metadata.to_csv('sankey.csv', index=False)

# # Compare the new CSV file with the previous one
# def compare_csv_files(file1, file2):
#     df1 = pd.read_csv(file1)
#     df2 = pd.read_csv(file2)
#     if df1.equals(df2):
#         print("The two CSV files are the same.")
#     else:
#         print("The two CSV files are different.")

# # Compare 'enginar.csv' with 'modified_vss_compact_metadata_test.csv'
# compare_csv_files('sankey.csv', 'modified_vss_compact_metadata_test.csv')
