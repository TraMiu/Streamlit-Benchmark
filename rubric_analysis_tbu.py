import json
import os
from collections import defaultdict
import pandas as pd

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
INPUT_FILENAME = '2025-05-07-06-14-12_oss_eval.jsonl'  # Your 5000 sample file
OUTPUT_DIR = 'rubric_analysis' # Where to save the lists

# ---------------------------------------------------------
# 1. SETUP DUMMY DATA (For demonstration purposes only)
# If you have your real file, you can skip/comment out this block
# ---------------------------------------------------------
def create_dummy_file():
    # Using the data from your prompt to create a valid jsonl file
    data_sample = {
        "rubrics": [
            {"criterion": "Correctly states that compression depth remains...", "points": 10, "tags": ["level:example", "axis:accuracy"]},
            {"criterion": "Cites standard epinephrine dosing...", "points": 9, "tags": ["level:example", "axis:accuracy"]},
            {"criterion": "Asks about the history of knee injury...", "points": 7, "tags": ["level:example", "axis:context_awareness"]},
            {"criterion": "Fails to mention waveform capnography...", "points": -4, "tags": ["level:example", "axis:completeness"]},
            {"criterion": "The response has no factually incorrect information.", "points": 5, "tags": ["cluster:hedging", "axis:accuracy"]},
        ]
    }
    
    # Writing this sample 10 times to simulate a larger file
    with open(INPUT_FILENAME, 'w', encoding='utf-8') as f:
        for _ in range(10):
            f.write(json.dumps(data_sample) + '\n')
    print(f"Created dummy file: {INPUT_FILENAME}")

if not os.path.exists(INPUT_FILENAME):
    create_dummy_file()

# ---------------------------------------------------------
# 2. DATA PROCESSING LOGIC
# ---------------------------------------------------------
def process_rubrics(filename):
    # Dictionary to store rubrics: { 'accuracy': [list of criteria], ... }
    grouped_rubrics = defaultdict(list)
    
    # specific set to avoid duplicates (since 5000 samples might repeat rubrics)
    seen_criteria = set()

    print(f"Reading {filename}...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            try:
                data = json.loads(line)
                
                # Check if rubrics exist in this line
                if 'rubrics' not in data:
                    continue

                for rubric in data['rubrics']:
                    criterion = rubric.get('criterion', '')
                    tags = rubric.get('tags', [])
                    points = rubric.get('points', 0)

                    # Create a unique signature to avoid duplicates
                    # signature = text + points
                    signature = f"{criterion}_{points}"
                    
                    if signature in seen_criteria:
                        continue
                    
                    seen_criteria.add(signature)

                    # Find the axis tag
                    axis = "unknown"
                    for tag in tags:
                        if tag.startswith("axis:"):
                            axis = tag.split("axis:")[1]
                            break
                    
                    # Store the relevant data
                    rubric_data = {
                        "points": points,
                        "criterion": criterion,
                        "tags": tags
                    }
                    
                    grouped_rubrics[axis].append(rubric_data)

            except json.JSONDecodeError:
                print(f"Skipping error on line {line_num}")

    return grouped_rubrics

# ---------------------------------------------------------
# 3. VISUALIZATION & EXPORT
# ---------------------------------------------------------
def visualize_and_export(grouped_rubrics):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    summary_data = []

    print(f"\n{'='*60}")
    print(f"RUBRIC ANALYSIS REPORT")
    print(f"{'='*60}\n")

    for axis, items in grouped_rubrics.items():
        # 1. Collect Summary Stats
        summary_data.append({
            "Axis Name": axis,
            "Unique Rubrics": len(items),
            "Avg Points": round(sum(i['points'] for i in items) / len(items), 2)
        })

        # 2. Export to file
        output_file = os.path.join(OUTPUT_DIR, f"rubrics_{axis}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"RUBRIC AXIS: {axis.upper()}\n")
            f.write(f"Total Unique Items: {len(items)}\n")
            f.write("-" * 80 + "\n\n")
            
            # Sort by points (highest to lowest) for better reading
            sorted_items = sorted(items, key=lambda x: x['points'], reverse=True)
            
            for item in sorted_items:
                f.write(f"POINTS: {item['points']}\n")
                f.write(f"CRITERION: {item['criterion']}\n")
                f.write(f"TAGS: {item['tags']}\n")
                f.write("\n")
        
        print(f"-> Saved {len(items)} items to {output_file}")

    # 3. Visualize Summary Table using Pandas
    if summary_data:
        df = pd.DataFrame(summary_data)
        print("\nSUMMARY TABLE:")
        print(df.to_string(index=False))
        
        # Optional: Show 3 random examples from the most populated axis
        largest_axis = df.loc[df['Unique Rubrics'].idxmax()]['Axis Name']
        print(f"\n--- Examples from largest axis: '{largest_axis}' ---")
        for i in grouped_rubrics[largest_axis][:3]:
            print(f"[{i['points']} pts] {i['criterion'][:100]}...")
    else:
        print("No rubrics found.")

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1. Process
    rubric_groups = process_rubrics(INPUT_FILENAME)
    
    # 2. Visualize & Save
    visualize_and_export(rubric_groups)
    
    print(f"\nDone! Check the '{OUTPUT_DIR}' folder for your files.")
