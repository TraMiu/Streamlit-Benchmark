# import json
# import csv
# import torch
# import pandas as pd
# from sentence_transformers import SentenceTransformer, util

# # --- CONFIGURATION ---
# FILE_PATH_A = 'farm2vets topics/husbandry_data.json'
# FILE_PATH_B = 'healthbench/turns/group_2_5_turns.jsonl'
# OUTPUT_JSON = 'husbandry_group_2_5_turn_top5_matches.json'
# OUTPUT_CSV = 'husbandry_group_2_5_turn_top5_matches.csv'
# MODEL_NAME = 'all-MiniLM-L6-v2'
# TOP_K = 5

# def load_data_a(file_path):
#     texts = []
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#         for item in data:
#             combined_text = (
#                 f"Question: {item.get('question', '')}\n"
#                 f"Answer: {item.get('answer', '')}\n"
#                 f"Notes: {item.get('notes', '')}"
#             )
#             texts.append(combined_text)
#     except FileNotFoundError:
#         print(f"Error: File {file_path} not found.")
#         return [], []
#     return texts, data

# def load_data_b(file_path):
#     texts = []
#     raw_data = []
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 line = line.strip()
#                 if not line: continue
#                 try:
#                     item = json.loads(line)
#                     raw_data.append(item)
                    
#                     conversation_text = ""
#                     if 'prompt' in item:
#                         for turn in item['prompt']:
#                             role = turn.get('role', 'unknown')
#                             content = turn.get('content', '')
#                             conversation_text += f"{role}: {content}\n"
                    
#                     if item.get('ideal_completions_data') is None:
#                         completion = ""
#                     else: 
#                         completion = item.get('ideal_completions_data', {}).get('ideal_completion', '')
#                     texts.append(f"{conversation_text}\nResponse:\n{completion}")
#                 except json.JSONDecodeError:
#                     continue
#     except FileNotFoundError:
#         print(f"Error: File {file_path} not found.")
#         return [], []
#     return texts, raw_data

# # --- MAIN EXECUTION ---

# print(f"1. Loading Model: {MODEL_NAME}...")
# device = 'cuda' if torch.cuda.is_available() else 'cpu'
# model = SentenceTransformer(MODEL_NAME, device=device)

# print("2. Loading Data...")
# texts_a, raw_a = load_data_a(FILE_PATH_A)
# texts_b, raw_b = load_data_b(FILE_PATH_B)

# if not texts_a or not texts_b:
#     print("Stopping: Data missing.")
#     exit()

# print(f"   -> List A: {len(texts_a)} items")
# print(f"   -> List B: {len(texts_b)} items")

# # 3. Batch Encoding
# print("3. Generating Embeddings...")
# embeddings_a = model.encode(texts_a, convert_to_tensor=True, batch_size=64, show_progress_bar=True)
# embeddings_b = model.encode(texts_b, convert_to_tensor=True, batch_size=64, show_progress_bar=True)

# # 4. Calculate Matrix
# print("4. Calculating Similarity Matrix...")
# similarity_matrix = util.cos_sim(embeddings_a, embeddings_b)

# # 5. Extract Top K Matches
# print(f"5. Extracting Top {TOP_K} matches...")
# json_results = []
# csv_rows = []

# similarity_matrix = similarity_matrix.cpu()

# for idx_a in range(len(texts_a)):
#     scores = similarity_matrix[idx_a]
    
#     # Get top K indices and values
#     k = min(TOP_K, len(texts_b))
#     top_values, top_indices = torch.topk(scores, k=k)
    
#     # Prepare row for CSV
#     # Identifier for A (defaulting to row index if 'number' is missing)
#     id_a = raw_a[idx_a].get('number', f"row_{idx_a}")
    
#     csv_row = {'Item A ID': id_a}
#     match_list_json = []

#     for rank, idx_b_tensor in enumerate(top_indices):
#         idx_b = idx_b_tensor.item()
#         score = top_values[rank].item()
        
#         # Extract Prompt ID from B (fallback to index if missing)
#         b_prompt_id = raw_b[idx_b].get('prompt_id', f"index_{idx_b}")
        
#         # Add to JSON list
#         match_list_json.append({
#             "rank": rank + 1,
#             "score": round(score, 4),
#             "prompt_id": b_prompt_id,
#             "snippet": texts_b[idx_b][:100] + "..."
#         })
        
#         # Add to CSV Row (Dynamic columns: Top 1 Score, Top 1 ID, etc.)
#         csv_row[f'Top {rank+1} Score'] = round(score, 4)
#         csv_row[f'Top {rank+1} ID'] = b_prompt_id

#     # Append to collections
#     json_results.append({
#         "item_a_id": id_a,
#         "question": raw_a[idx_a].get('question', ''),
#         "matches": match_list_json
#     })
#     csv_rows.append(csv_row)

# # 6. Save Files
# print("6. Saving output files...")

# # Save JSON
# with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
#     json.dump(json_results, f, indent=2)

# # Save CSV using Pandas (handles column ordering easily)
# df = pd.DataFrame(csv_rows)
# df.to_csv(OUTPUT_CSV, index=False)

# print(f"Done. Saved to {OUTPUT_JSON} and {OUTPUT_CSV}")


import json
import csv
import torch
import pandas as pd
import random
from sentence_transformers import SentenceTransformer, util

# --- CONFIGURATION ---
FILE_PATH_A = 'farm2vets topics/28-01-2026 conversation QAs.json'
FILE_PATH_B = 'healthbench/turns/group_2_5_turns.jsonl'

# Outputs
OUTPUT_JSON_TOP5 = '28-01-2026 conversation QAs_group_2_5_turn_top5_matches.json'
OUTPUT_CSV_TOP5 = '28-01-2026 conversation QAs_group_2_5_turn_top5_matches.csv'
OUTPUT_MERGED_BEST = '28-01-2026 conversation QAs_best_matches_enriched.json' # <--- NEW FILE

MODEL_NAME = 'all-MiniLM-L6-v2'
TOP_K = 5

def sample_num_turns():
    """
    Sample an odd number of turns so the conversation ends with User.
    Allowed values: 1, 3, 5, 7
    """
    return random.choice([0, 1, 2, 3, 4])

def load_data_a(file_path):
    texts = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            combined_text = (
                f"Question: {item.get('question', '')}\n"
                f"Answer: {item.get('answer', '')}\n"
                f"Notes: {item.get('notes', '')}"
            )
            texts.append(combined_text)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return [], []
    return texts, data

def load_data_b(file_path):
    texts = []
    raw_data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    item = json.loads(line)
                    raw_data.append(item)
                    
                    conversation_text = ""
                    if 'prompt' in item:
                        for turn in item['prompt']:
                            role = turn.get('role', 'unknown')
                            content = turn.get('content', '')
                            conversation_text += f"{role}: {content}\n"
                    
                    completion = item.get('ideal_completions_data', {}).get('ideal_completion', '') if item.get('ideal_completions_data') else ""
                    texts.append(f"{conversation_text}\nResponse:\n{completion}")
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return [], []
    return texts, raw_data

# --- MAIN EXECUTION ---

print(f"1. Loading Model: {MODEL_NAME}...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer(MODEL_NAME, device=device)

print("2. Loading Data...")
texts_a, raw_a = load_data_a(FILE_PATH_A)
texts_b, raw_b = load_data_b(FILE_PATH_B)

if not texts_a or not texts_b:
    print("Stopping: Data missing.")
    exit()

print(f"   -> List A: {len(texts_a)} items")
print(f"   -> List B: {len(texts_b)} items")

# 3. Batch Encoding
print("3. Generating Embeddings...")
embeddings_a = model.encode(texts_a, convert_to_tensor=True, batch_size=64, show_progress_bar=True)
embeddings_b = model.encode(texts_b, convert_to_tensor=True, batch_size=64, show_progress_bar=True)

# 4. Calculate Matrix
print("4. Calculating Similarity Matrix...")
similarity_matrix = util.cos_sim(embeddings_a, embeddings_b)

# 5. Extract Matches & Build Merged List
print(f"5. Extracting Matches...")
json_results_top5 = []
csv_rows = []
merged_best_matches = [] # List for the new JSON file

similarity_matrix = similarity_matrix.cpu()

for idx_a in range(len(texts_a)):
    scores = similarity_matrix[idx_a]
    
    # Get top K indices and values
    k = min(TOP_K, len(texts_b))
    top_values, top_indices = torch.topk(scores, k=k)
    
    id_a = raw_a[idx_a].get('number', f"row_{idx_a}")
    
    # --- LOGIC FOR NEW MERGED FILE (Best Match Only) ---
    # The first item in top_indices is the best match (Top 1)
    best_match_idx = top_indices[sample_num_turns()].item()
    best_match_prompt_id = raw_b[best_match_idx].get('prompt_id', f"index_{best_match_idx}")
    
    # Create a copy of the original item from A so we don't modify raw_a
    enriched_item = raw_a[idx_a].copy()
    # Add the prompt_id from B
    enriched_item['prompt_id'] = best_match_prompt_id
    # Optional: You might want to include the score to know how good the match was
    enriched_item['similarity_score'] = round(top_values[0].item(), 4)
    
    merged_best_matches.append(enriched_item)
    # ----------------------------------------------------

    # --- LOGIC FOR EXISTING OUTPUTS (Top 5 JSON/CSV) ---
    csv_row = {'Item A ID': id_a}
    match_list_json = []

    for rank, idx_b_tensor in enumerate(top_indices):
        idx_b = idx_b_tensor.item()
        score = top_values[rank].item()
        b_prompt_id = raw_b[idx_b].get('prompt_id', f"index_{idx_b}")
        
        match_list_json.append({
            "rank": rank + 1,
            "score": round(score, 4),
            "prompt_id": b_prompt_id,
            "snippet": texts_b[idx_b][:100] + "..."
        })
        
        csv_row[f'Top {rank+1} Score'] = round(score, 4)
        csv_row[f'Top {rank+1} ID'] = b_prompt_id

    json_results_top5.append({
        "item_a_id": id_a,
        "question": raw_a[idx_a].get('question', ''),
        "matches": match_list_json
    })
    csv_rows.append(csv_row)

# 6. Save Files
print("6. Saving output files...")

# 1. Save Original Detailed JSON
with open(OUTPUT_JSON_TOP5, 'w', encoding='utf-8') as f:
    json.dump(json_results_top5, f, indent=2)

# 2. Save CSV
df = pd.DataFrame(csv_rows)
df.to_csv(OUTPUT_CSV_TOP5, index=False)

# 3. Save NEW Enriched JSON (Item A + Best Prompt ID)
with open(OUTPUT_MERGED_BEST, 'w', encoding='utf-8') as f:
    json.dump(merged_best_matches, f, indent=2, ensure_ascii=False)

print(f"Done.")
print(f" -> Top 5 Details: {OUTPUT_JSON_TOP5}")
print(f" -> Top 5 CSV:     {OUTPUT_CSV_TOP5}")
print(f" -> Best Match ID: {OUTPUT_MERGED_BEST}")
