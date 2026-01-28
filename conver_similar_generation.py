# import json

# def generate_veterinary_prompts(json_a_path, jsonl_b_path):
#     # 1. Read File B (JSONL) and create a lookup dictionary
#     #    Key: prompt_id, Value: The full data object
#     conversation_map = {}
    
#     try:
#         with open(jsonl_b_path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 if not line.strip(): continue # Skip empty lines
#                 data = json.loads(line)
                
#                 # Store by prompt_id for fast retrieval
#                 if 'prompt_id' in data:
#                     conversation_map[data['prompt_id']] = data
#     except FileNotFoundError:
#         return [f"Error: File B not found at {jsonl_b_path}"]

#     # 2. Read File A (JSON List)
#     try:
#         with open(json_a_path, 'r', encoding='utf-8') as f:
#             qa_list = json.load(f)
#     except FileNotFoundError:
#         return [f"Error: File A not found at {json_a_path}"]

#     generated_outputs = []

#     # 3. Iterate through Q&A records in File A
#     for qa_record in qa_list:
#         target_id = qa_record.get('prompt_id')
        
#         # Check if we have a matching conversation in File B
#         if target_id in conversation_map:
#             match_data = conversation_map[target_id]
            
#             # --- Extract Medical Domain Example (Variable Turns) ---
#             formatted_dialogue_parts = []
            
#             # We iterate strictly through the 'prompt' list as shown in your image
#             # This handles User -> Assistant -> User sequences automatically
#             if 'prompt' in match_data and isinstance(match_data['prompt'], list):
#                 for message in match_data['prompt']:
#                     raw_role = message.get('role', 'User')
#                     content = message.get('content', '').strip()
                    
#                     # Capitalize role for formatting (e.g., 'user' -> 'User', 'assistant' -> 'Assistant')
#                     display_role = raw_role.capitalize()
                    
#                     formatted_dialogue_parts.append(f"{display_role}: {content}")
            
#             # Join the parts with newlines
#             formatted_dialogue = "\n".join(formatted_dialogue_parts)

#             # If the list was empty or missing, provide a fallback
#             if not formatted_dialogue:
#                 formatted_dialogue = "[No conversation turns found in 'prompt' list]"

#             # --- Construct the Final Output String ---
#             output_text = f"""Task:
# Generate a natural, multi-turn conversation for a veterinary chatbot using the provided Core Q&A and Professional Vet Notes. You can learn from a realistic conversation in medical domain.

# Medical Domain Example:
# {formatted_dialogue}

# Core Q&A:
# Question: {qa_record.get('question')}

# Answer: {qa_record.get('answer')}

# Professional Vet Notes (Background Only):
# {qa_record.get('notes')}

# Conversation Guidelines:
# - The conversation should be between 2-7 turns long.
# - Write a realistic back-and-forth conversation (User ↔ Assistant)
# - The assistant should respond progressively, not all at once
# - Use the notes selectively and creatively; do not repeat them
# - Use questions and answers as reference, not verbatim
# - Maintain professional veterinary tone
# - Avoid medical diagnosis or prescriptions unless explicitly allowed


# Ending Constraint:
# The conversation must end with a user turn, not the assistant

# Output Format:
# User:
# Vet:
# ...
# User:
# """
#             generated_outputs.append(output_text)
#         else:
#             # Optional: Print warning for debugging
#             # print(f"Warning: No matching conversation found in File B for prompt_id: {target_id}")
#             pass

#     return generated_outputs

# # --- USAGE EXAMPLE ---

# if __name__ == "__main__":
#     # Using the filenames you specified
#     file_a = 'husbandry_best_matches_enriched.json'
#     file_b = 'healthbench/2025-05-07-06-14-12_oss_eval.jsonl'
    
#     output_texts = generate_veterinary_prompts(file_a, file_b)
#     print(f"Generated {len(output_texts)} prompts.")
    
#     #TODO: Write outputs to a file 

#     #TODO: Use output_texts to prompt OpenAI API for new conversations generations

#     #TODO: read OpanAI API Responses and save to a copy of File A with new conversations 

import json
import re
import os
from openai import OpenAI  # Uncomment when ready to use

# ---------------------------------------------------------
# 1. PARSING HELPER
# ---------------------------------------------------------

import random

def sample_num_turns():
    """
    Sample an odd number of turns so the conversation ends with User.
    Allowed values: 1, 3, 5, 7
    """
    return random.choice([1, 3, 5, 7, 9])

def parse_generated_text(text):
    """
    Parses the text output from the LLM:
      User: I have a pig with a cough.
      Vet: check for fever.
      User: Okay.
    
    Returns a list of dicts:
      [
        {"role": "user", "content": "I have a pig with a cough."},
        {"role": "assistant", "content": "check for fever."},
        {"role": "user", "content": "Okay."}
      ]
    """
    conversations = []
    
    # Regex to find lines starting with "User:" or "Vet:"
    # (?m) enables multiline matching, ^ matches start of line
    pattern = r'(?m)^(User|Vet):\s*'
    
    # Split the text by the markers. 
    # capturing groups in split() include the separators in the result list.
    parts = re.split(pattern, text)
    
    # parts[0] is usually empty (text before first marker)
    # Then it follows the pattern: [Marker, Content, Marker, Content...]
    for i in range(1, len(parts), 2):
        role_marker = parts[i].strip()
        content = parts[i+1].strip()
        
        # Map "Vet" to "assistant" and "User" to "user"
        role = "assistant" if role_marker == "Vet" else "user"
        
        if content:
            conversations.append({
                "content": content,
                "role": role
            })
            
    return conversations

# ---------------------------------------------------------
# 2. PROMPT GENERATOR (Modified to return context)
# ---------------------------------------------------------
def generate_veterinary_prompts_with_context(json_a_path, jsonl_b_path):
    conversation_map = {}
    
    # Load File B (JSONL)
    try:
        with open(jsonl_b_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if 'prompt_id' in data:
                    conversation_map[data['prompt_id']] = data
    except FileNotFoundError:
        print(f"Error: File B not found at {jsonl_b_path}")
        return []

    # Load File A (JSON List)
    try:
        with open(json_a_path, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
    except FileNotFoundError:
        print(f"Error: File A not found at {json_a_path}")
        return []

    results = []

    for qa_record in qa_list:
        target_id = qa_record.get('prompt_id')
        
        if target_id in conversation_map:
            match_data = conversation_map[target_id]
            
            # Extract Example Dialogue
            formatted_dialogue_parts = []
            if 'prompt' in match_data and isinstance(match_data['prompt'], list):
                for message in match_data['prompt']:
                    raw_role = message.get('role', 'User')
                    content = message.get('content', '').strip()
                    display_role = raw_role.capitalize() # User or Assistant
                    formatted_dialogue_parts.append(f"{display_role}: {content}")
            
            formatted_dialogue = "\n".join(formatted_dialogue_parts)
            if not formatted_dialogue:
                formatted_dialogue = "[No conversation turns found in 'prompt' list]"

            # Construct Prompt
            prompt_text = f"""Task:
Generate a natural, multi-turn conversation for a veterinary chatbot using the provided Core Q&A and Professional Vet Notes. You can learn from a realistic conversation in medical domain.

Medical Domain Example:
{formatted_dialogue}

Core Q&A:
Question: {qa_record.get('question')}

Answer: {qa_record.get('answer')}

Professional Vet Notes (Background Only):
{qa_record.get('notes')}

Conversation Guidelines:
- The conversation should be {sample_num_turns()} turns long.
- Write a realistic back-and-forth conversation (User ↔ Assistant)
- The assistant should respond progressively, not all at once
- Use the notes selectively and creatively; do not repeat them
- Use questions and answers as reference, not verbatim
- Maintain professional veterinary tone
- Avoid medical diagnosis or prescriptions unless explicitly allowed

Final User Turn Constraint (IMPORTANT):
- The final user turn MUST be a substantive follow-up question or scenario.
- The final user turn MUST require reasoning, clarification, or guidance from the vet.
- DO NOT end with gratitude, acknowledgment, or closure phrases (e.g., "thank you", "got it", "okay").
- The final user turn should introduce:
  - uncertainty, OR
  - a practical concern, OR
  - a conditional scenario, OR
  - a request for clarification or next steps.

Ending Constraint:
The conversation must end with a USER turn that invites a veterinary response.

Output Format:
User:
Vet:
...
User:
"""
            # Store tuple: (The prompt string, The original record object)
            results.append((prompt_text, qa_record))
            
    return results

# ---------------------------------------------------------
# 3. MOCK API CALL (Replace with real OpenAI call)
# ---------------------------------------------------------
def call_openai_api(prompt_text):
    """
    Simulates an OpenAI API call. 
    Replace this with actual client.chat.completions.create()
    """
    # api_key = os.getenv("OPENAI_API")
    # if not api_key:
    #     raise RuntimeError("OPENAI_API not set in environment or .env")
    client = OpenAI(api_key="")
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.7
    )
    return response.choices[0].message.content

    # --- MOCK RESPONSE FOR TESTING ---
#     return """User: How often should I water my pigs in the summer?
# Vet: In the summer heat, continuous access is best. If that's not possible, aim for at least 3-4 times a day.
# User: Oh, I only do it twice right now. Is that bad?
# Vet: It might lead to dehydration. Pigs need 3-4 times as much water as food. Try adding an evening watering.
# User: Okay, I will try to add a trough for the evening."""


# ---------------------------------------------------------
# 4. MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    file_a = '28-01-2026 conversation QAs_best_matches_enriched.json'
    file_b = 'healthbench/2025-05-07-06-14-12_oss_eval.jsonl'
    output_file = '28-01-2026_final_conversations.json'

    # 1. Generate Prompts linked to Records
    prompt_data = generate_veterinary_prompts_with_context(file_a, file_b)
    print(f"Generated {len(prompt_data)} prompts. Starting API generation...")

    final_records = []

    # 2. Iterate and Call API
    for i, (prompt_text, original_record) in enumerate(prompt_data):
        print(f"Processing record {i+1}/{len(prompt_data)} (ID: {original_record.get('prompt_id')})...")
        
        try:
            # --- Call API ---
            raw_response = call_openai_api(prompt_text)
            
            # --- Parse Response ---
            new_conversation_structure = parse_generated_text(raw_response)
            
            # --- Update Record ---
            # Create a copy of the record to avoid mutating the original inadvertently
            new_record = original_record.copy()
            
            # Overwrite or add the 'prompt' field with the new conversation
            new_record['prompt'] = new_conversation_structure
            
            # Optional: Remove 'similarity_score' or other temporary fields if desired
            # if 'similarity_score' in new_record: del new_record['similarity_score']

            final_records.append(new_record)
            
        except Exception as e:
            print(f"Failed to process record {i+1}: {e}")

    # 3. Save to File A copy
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_records, f, indent=4, ensure_ascii=False)

    print(f"\nSuccess! Saved {len(final_records)} records with new conversations to '{output_file}'")
