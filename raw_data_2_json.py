# import pandas as pd
# import json

# def extract_to_json_pandas(input_file, output_file):
#     try:
#         # Read the CSV file
#         df = pd.read_csv(input_file)
        
#         # Clean column names (remove leading/trailing spaces)
#         df.columns = [c.strip() for c in df.columns]
        
#         # Filter out rows where 'Question' is empty (removes the empty ",,," row)
#         df = df.dropna(subset=['Question'], how='all')
        
#         # Select the specific columns
#         # Adjust column names here if they differ slightly in your actual file
#         target_columns = ["No.", "Question", "Answer", "Dr.Csaba's notes"]
        
#         # Check if columns exist
#         missing_cols = [c for c in target_columns if c not in df.columns]
#         if missing_cols:
#             print(f"Warning: Columns {missing_cols} not found. Available columns: {list(df.columns)}")
#             return

#         df = df[target_columns].copy()

#         # Rename columns to clean JSON keys
#         df.rename(columns={
#             "No.": "number",
#             "Question": "question",
#             "Answer": "answer",
#             "Csaba's notes": "notes"
#         }, inplace=True)

#         # Convert to a list of dictionaries
#         data = df.to_dict(orient='records')

#         # Write to JSON file
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=4)
            
#         print(f"Successfully extracted {len(data)} items to {output_file}")

#     except Exception as e:
#         print(f"An error occurred: {e}")

# # Usage
# csv_file_path = '28-01-2026 conversation QAs - Sheet1.csv' # Replace with your actual file path
# json_file_path = '28-01-2026 conversation QAs.json'
# extract_to_json_pandas(csv_file_path, json_file_path)

import pandas as pd
import json

def get_topic(number):
    """
    Returns the topic string based on the provided number.
    Handles potential float/string inputs by converting to int first.
    """
    try:
        n = int(number)
    except (ValueError, TypeError):
        return "Unknown"

    if 1 <= n <= 22:
        return "Facilities"
    elif 23 <= n <= 92:
        return "Husbandry"
    elif 93 <= n <= 165:
        return "Diseases and Treatments"
    elif 166 <= n <= 191:
        return "Vaccination"
    elif 192 <= n <= 212:
        return "Biosecurity"
    elif 213 <= n <= 225:
        return "General Management"
    else:
        return "Uncategorized"

def extract_to_json_pandas(input_file, output_file):
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Clean column names
        df.columns = [c.strip() for c in df.columns]
        
        # Filter out empty rows based on 'Question'
        df = df.dropna(subset=['Question'], how='all')
        
        # Define target columns (ensure these match your CSV exactly)
        # Note: I kept "Dr.Csaba's notes" based on your previous snippet, 
        # but renamed it to "notes" in the mapping below.
        target_columns = ["No.", "Question", "Answer", "Dr.Csaba's notes"]
        
        # Check if columns exist
        missing_cols = [c for c in target_columns if c not in df.columns]
        if missing_cols:
            print(f"Warning: Columns {missing_cols} not found. Available columns: {list(df.columns)}")
            return

        df = df[target_columns].copy()

        # Rename columns to clean JSON keys
        df.rename(columns={
            "No.": "number",
            "Question": "question",
            "Answer": "answer",
            "Dr.Csaba's notes": "notes" 
        }, inplace=True)

        # --- NEW STEP: Apply Topic Tags ---
        # We apply the helper function to the 'number' column to create a new 'topic' column
        df['topic'] = df['number'].apply(get_topic)

        # Convert to a list of dictionaries
        data = df.to_dict(orient='records')

        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully extracted {len(data)} items with topics to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage
csv_file_path = '28-01-2026 conversation QAs - Sheet1.csv' 
json_file_path = '28-01-2026 conversation QAs.json'
extract_to_json_pandas(csv_file_path, json_file_path)
