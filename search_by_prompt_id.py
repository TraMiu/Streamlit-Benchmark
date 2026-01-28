import streamlit as st
import json
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="JSONL Viewer",
    page_icon="🔍",
    layout="wide"
)

# --- cached Data Loading ---
@st.cache_data
def load_data(file_path):
    """
    Loads JSONL data and caches it so re-running the app is instant.
    Returns a dictionary keyed by prompt_id for O(1) lookup speed.
    """
    if not os.path.exists(file_path):
        return None
    
    data_map = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    pid = item.get('prompt_id')
                    if pid:
                        data_map[pid] = item
        return data_map
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return {}

# --- Sidebar: Configuration & Search ---
with st.sidebar:
    st.header("📂 Data Source")
    # Default file path; user can change this in the UI
    file_path = st.text_input("File Path (.jsonl)", value="healthbench/turns/group_2_5_turns.jsonl")
    
    st.divider()
    
    st.header("🔍 Search")
    # Using a text input for ID pasting
    search_query = st.text_input("Paste Prompt ID here:")
    
    # Optional: Add a dropdown if the dataset is small enough
    # st.divider()
    # show_all = st.checkbox("Show ID List")

# --- Main App Logic ---
if not file_path:
    st.warning("Please enter a file path in the sidebar.")
    st.stop()

# Load data
data_map = load_data(file_path)

if data_map is None:
    st.error(f"❌ File not found: `{file_path}`")
    st.info("Make sure the file exists in the same directory or provide the full path.")
    st.stop()

# --- Display Logic ---
if search_query:
    # Remove whitespace
    clean_id = search_query.strip()
    
    # Find the sample
    sample = data_map.get(clean_id)
    
    if sample:
        st.success(f"Found ID: `{clean_id}`")
        st.divider()

        # Create two columns: Chat (Left) vs Rubrics (Right)
        col1, col2 = st.columns([1.5, 1])

        # --- LEFT COLUMN: Conversation ---
        with col1:
            st.subheader("🗣️ Conversation History")
            prompt_data = sample.get('prompt', [])
            
            if isinstance(prompt_data, list):
                for msg in prompt_data:
                    role = msg.get('role', 'unknown').lower()
                    content = msg.get('content', '')
                    
                    # Streamlit has a built-in chat message component
                    with st.chat_message(role):
                        st.markdown(content)
            else:
                st.warning("No conversation format detected.")

        # --- RIGHT COLUMN: Rubrics ---
        with col2:
            st.subheader("📋 Grading Rubrics")
            rubrics = sample.get('rubrics', [])
            
            if rubrics:
                for i, r in enumerate(rubrics, 1):
                    # Use an expander for each rubric item to save space
                    points = r.get('points', 0)
                    color = "green" if points > 0 else "red"
                    
                    with st.expander(f"Criterion {i} (:bf-{color}[{points} pts])"):
                        st.markdown(f"**Description:**\n{r.get('criterion')}")
                        st.caption(f"**Tags:** {', '.join(r.get('tags', []))}")
            else:
                st.info("No rubrics found for this sample.")

            # Optional: Show 'Ideal Completion' if it exists
            ideal_data = sample.get('ideal_completions_data')
            if ideal_data:
                st.divider()
                st.subheader("✨ Ideal Completion")
                with st.expander("Show Ideal Response"):
                    st.write(ideal_data.get('ideal_completion'))

    else:
        st.error(f"❌ ID `{clean_id}` not found in the dataset.")
else:
    # Welcome Screen
    st.title("JSONL Data Viewer")
    st.markdown("""
    👈 **Start by pasting a Prompt ID in the sidebar.**
    
    This tool allows you to visually inspect:
    * The conversation turns
    * The grading rubrics
    * The ideal completions
    """)
    st.info(f"Loaded {len(data_map)} samples from `{file_path}`.")
