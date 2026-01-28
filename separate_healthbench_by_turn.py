import json
import os

def classify_conversations(input_file):
    # Define output filenames
    output_files = {
        "1_turn": "group_1_turn.jsonl",
        "2_5_turns": "group_2_5_turns.jsonl",
        "6_10_turns": "group_6_10_turns.jsonl",
        "11_20_turns": "group_11_20_plus_turns.jsonl"
    }

    # Initialize counters for statistics
    stats = {key: 0 for key in output_files}
    
    # Open all output files in append mode (or write mode to clear previous)
    # We keep file handles open for efficiency instead of opening/closing on every line
    handles = {key: open(filename, 'w', encoding='utf-8') for key, filename in output_files.items()}

    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            for line_number, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    
                    # 1. Calculate number of turns
                    # We assume 'prompt' is a list of dictionaries representing the conversation
                    if 'prompt' in data and isinstance(data['prompt'], list):
                        turn_count = len(data['prompt'])
                    else:
                        print(f"Warning: Line {line_number} has no valid 'prompt' list. Skipping.")
                        continue

                    # 2. Classify based on turn count
                    target_key = None
                    
                    if turn_count == 1:
                        target_key = "1_turn"
                    elif 2 <= turn_count <= 5:
                        target_key = "2_5_turns"
                    elif 6 <= turn_count <= 10:
                        target_key = "6_10_turns"
                    elif turn_count >= 11:
                        # You mentioned 11-20, but usually this catches everything above 11
                        # If you strictly want to exclude >20, add a check here.
                        # For now, I'll treat this as 11+
                        target_key = "11_20_turns"
                    
                    # 3. Write to the appropriate file
                    if target_key:
                        handles[target_key].write(line + '\n')
                        stats[target_key] += 1
                    else:
                        # Should strictly not happen with the logic above unless turns is 0
                        print(f"Line {line_number} has 0 turns. Skipping.")

                except json.JSONDecodeError:
                    print(f"Error: Line {line_number} is not valid JSON. Skipping.")

    finally:
        # Close all output file handles
        for handle in handles.values():
            handle.close()

    # Print summary
    print("-" * 30)
    print("Classification Complete.")
    print("-" * 30)
    for key, count in stats.items():
        print(f"{key.replace('_', ' ').title()}: {count} items")

# --- Usage ---
# Replace 'data.jsonl' with your actual filename
input_filename = 'healthbench/2025-05-07-06-14-12_oss_eval.jsonl'

if os.path.exists(input_filename):
    classify_conversations(input_filename)
else:
    # Creating a dummy file for demonstration if you run this immediately
    print(f"File '{input_filename}' not found. Please ensure your file exists.")
