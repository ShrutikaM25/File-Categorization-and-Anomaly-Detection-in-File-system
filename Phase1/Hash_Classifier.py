import pandas as pd
import pickle

# Load the cleaned dataset
df = pd.read_csv('cleaned_file_extensions.csv')

# Normalize the columns: lowercase, strip whitespace, and remove leading dot from Extension.
df['Extension'] = df['Extension'].astype(str).str.lower().str.strip().str.lstrip('.')
df['MIME type'] = df['MIME type'].astype(str).str.lower().str.strip()
df['Category'] = df['Category'].astype(str).str.lower().str.strip()

# Function to encode a column
def encode_column(column):
    unique_values = column.unique()
    value_to_index = {value: idx for idx, value in enumerate(unique_values)}
    return value_to_index

# Encode the columns
ext_to_idx = encode_column(df['Extension'])
df['Extension_encoded'] = df['Extension'].map(ext_to_idx)

mime_to_idx = encode_column(df['MIME type'])
df['MIME_encoded'] = df['MIME type'].map(mime_to_idx)

category_to_idx = encode_column(df['Category'])
df['Category_encoded'] = df['Category'].map(category_to_idx)

idx_to_category = {v: k for k, v in category_to_idx.items()}

# Create a dictionary for hash-based mapping
prediction_map = {
    (row['Extension_encoded'], row['MIME_encoded']): row['Category_encoded']
    for _, row in df.iterrows()
}

# Validation function
def evaluate_hash_mapping(X, y):
    correct = 0
    for i in range(len(X)):
        feature_pair = (X.iloc[i]['Extension_encoded'], X.iloc[i]['MIME_encoded'])
        predicted_category = prediction_map.get(feature_pair, -1)
        if predicted_category == y.iloc[i]:
            correct += 1

    accuracy = correct / len(X)
    print(f"Correct: {correct}")
    print(f"Len X: {len(X)}")
    print(f"Accuracy: {accuracy:.4f}")

# Prepare input and output for validation
X = df[['Extension_encoded', 'MIME_encoded']]
y = df['Category_encoded']

evaluate_hash_mapping(X, y)

# Save the hash mappings
hash_mappings = {
    'ext_to_idx': ext_to_idx,
    'mime_to_idx': mime_to_idx,
    'category_to_idx': category_to_idx,
    'idx_to_category': idx_to_category,
    'prediction_map': prediction_map
}

with open('hash_mappings.pkl', 'wb') as file:
    pickle.dump(hash_mappings, file)
