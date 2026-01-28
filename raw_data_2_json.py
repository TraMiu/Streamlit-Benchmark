import pandas as pd
import json

def extract_to_json_pandas(input_file, output_file):
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Clean column names (remove leading/trailing spaces)
        df.columns = [c.strip() for c in df.columns]
        
        # Filter out rows where 'Question' is empty (removes the empty ",,," row)
        df = df.dropna(subset=['Question', 'Csaba\'s notes'])
        
        # Select the specific columns
        # Adjust column names here if they differ slightly in your actual file
        target_columns = ["No.", "Question", "Answer", "Csaba's notes"]
        
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
            "Csaba's notes": "notes"
        }, inplace=True)

        # Convert to a list of dictionaries
        data = df.to_dict(orient='records')

        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully extracted {len(data)} items to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage
csv_file_path = 'husbandry.csv' # Replace with your actual file path
json_file_path = 'husbandry_data.json'
extract_to_json_pandas(csv_file_path, json_file_path)
