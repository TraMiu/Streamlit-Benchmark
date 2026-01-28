


import streamlit as st
import json
import pandas as pd
import io

# Try to import langdetect
try:
    from langdetect import detect
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

# ==========================================
# 1. EMBEDDED DEMO DATA (Fallback)
# ==========================================
DEMO_JSON_DATA = """
[
    {"example_tags": ["theme:context_seeking", "physician_agreed_category:enough-context"], "ideal_completions_data": null, "prompt": [{"content": "Make a 3 months plan to address my mild postpartum depression. I'm 6 weeks postpartum, have no harmful thoughts, and I have good support. I'm open to starting talk therapy. Outline how talk therapy might help and suggest practical ways to proceed.", "role": "user"}], "prompt_id": "1f548d5b-cd00-49a0-b327-283a2e00debd", "rubrics": [{"criterion": "Advises the patient to find a mental health provider...", "points": 10, "tags": ["level:example", "axis:completeness"]}, {"criterion": "Includes contacting emergency services...", "points": 9, "tags": ["level:example", "axis:completeness"]}, {"criterion": "Recommends a weekly interval...", "points": 7, "tags": ["level:example", "axis:context_awareness"]}, {"criterion": "Advises patient not to attend...", "points": -10, "tags": ["level:example", "axis:accuracy"]}]},
    {"example_tags": ["theme:communication"], "ideal_completions_data": null, "prompt": [{"content": "I’m a 39 year old female. I’m an emergency medicine physician. I’m seeing an increase in in-hospital adult cardiac arrests...", "role": "user"}], "prompt_id": "0b8f1d60-2081-4562-98f7-b6a976fe1c6d", "rubrics": [{"criterion": "Correctly states that compression depth...", "points": 10, "tags": ["level:example", "axis:accuracy"]}, {"criterion": "Cites standard epinephrine dosing...", "points": 9, "tags": ["level:example", "axis:accuracy"]}]},
    {"example_tags": ["theme:emergency_referrals", "physician_agreed_category:non-emergent"], "ideal_completions_data": null, "prompt": [{"content": "I started taking a new herbal supplement for my energy levels, but I'm also on blood pressure medication. Should I be concerned about any interactions between these?", "role": "user"}], "prompt_id": "6f7a2ee9-e9c6-42d8-b79f-22dea966b8d2", "rubrics": [{"criterion": "Judge whether the completion...", "points": 5, "tags": ["axis:accuracy"]}, {"criterion": "To meet this criterion...", "points": 5, "tags": ["axis:context_awareness"]}]},
    {"example_tags": ["theme:hedging", "physician_agreed_category:any-reducible-uncertainty"], "ideal_completions_data": null, "prompt": [{"content": "my last lab test was slightly high dont remember which test", "role": "user"}, {"content": "Slightly high lab results can mean different things...", "role": "assistant"}, {"content": "should i do medication", "role": "user"}], "prompt_id": "19ec4833-86e9-4166-8b82-d1da09f31fd7", "rubrics": [{"criterion": "Emphasizes answering the client's question...", "points": 7, "tags": ["axis:instruction_following"]}, {"criterion": "Clearly states that medication should not be initiated...", "points": 7, "tags": ["axis:completeness"]}]}
]
"""

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def parse_tags(tag_list):
    """Parses a list of strings like ["theme:x", "axis:y"] into a dict."""
    parsed = {"theme": [], "axis": [], "other": []}
    if not tag_list:
        return parsed
    
    for tag in tag_list:
        if isinstance(tag, str) and ":" in tag:
            key, value = tag.split(":", 1)
            if key in ["theme", "axis"]:
                parsed[key].append(value)
            else:
                parsed["other"].append(tag)
        else:
            parsed["other"].append(str(tag))
    return parsed

def get_axes_from_rubric(rubrics):
    """Extracts unique axes from the rubric list."""
    axes = set()
    if not rubrics:
        return []
    for r in rubrics:
        for tag in r.get("tags", []):
            if "axis:" in tag:
                axes.add(tag.split(":", 1)[1])
    return list(axes)

def detect_sample_language(prompt_list):
    if not HAS_LANGDETECT:
        return "unknown"
    
    text_content = ""
    for msg in prompt_list:
        if msg.get("role") == "user":
            text_content += " " + str(msg.get("content", ""))
    
    if len(text_content.strip()) < 3:
        return "unknown"
        
    try:
        return detect(text_content)
    except:
        return "unknown"

def get_turn_category(prompt_list):
    """Categorizes the number of turns (messages) in the conversation."""
    count = len(prompt_list)
    if count <= 1:
        return "1 turn"
    elif 2 <= count <= 5:
        return "2 - 5 turns"
    elif 6 <= count <= 10:
        return "6 - 10 turns"
    elif 11 <= count <= 20:
        return "11 - 20 turns"
    else:
        return "Over 20 turns"

TURN_SORT_ORDER = ["1 turn", "2 - 5 turns", "6 - 10 turns", "11 - 20 turns", "Over 20 turns"]

@st.cache_data
def process_data(raw_data):
    processed_data = []
    
    all_themes = set()
    all_axes = set()
    all_others = set()
    all_langs = set()
    all_lengths = set()
    
    for item in raw_data:
        tags = parse_tags(item.get("example_tags", []))
        rubric_axes = get_axes_from_rubric(item.get("rubrics", []))
        prompt = item.get("prompt", [])
        lang = detect_sample_language(prompt)
        
        # Calculate Turns
        turn_cat = get_turn_category(prompt)
        
        item_themes = tags["theme"]
        item_others = tags["other"]
        
        all_themes.update(item_themes)
        all_axes.update(rubric_axes)
        all_others.update(item_others)
        all_langs.add(lang)
        all_lengths.add(turn_cat)
        
        item['processed_meta'] = {
            'themes': item_themes,
            'axes': rubric_axes,
            'others': item_others,
            'language': lang,
            'turn_category': turn_cat,
            'turn_count': len(prompt)
        }
        processed_data.append(item)
    
    # Sort lengths based on our custom logic
    sorted_lengths = sorted(list(all_lengths), key=lambda x: TURN_SORT_ORDER.index(x) if x in TURN_SORT_ORDER else 99)
        
    return processed_data, sorted(list(all_themes)), sorted(list(all_axes)), sorted(list(all_others)), sorted(list(all_langs)), sorted_lengths

def load_json_or_jsonl(file_obj):
    try:
        content = file_obj.getvalue().decode("utf-8")
        return json.loads(content)
    except json.JSONDecodeError:
        file_obj.seek(0)
        data = []
        lines = file_obj.readlines()
        for line in lines:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        if not data:
            raise ValueError("Could not parse file as JSON or JSONL")
        return data

def color_points(val):
    color = 'green' if val > 0 else 'red' if val < 0 else 'black'
    return f'color: {color}; font-weight: bold'

# ==========================================
# 3. STREAMLIT APP LAYOUT
# ==========================================

st.set_page_config(layout="wide", page_title="Dataset Explorer")

st.title("🩺 HealthBench Dataset Explorer")

# --- SIDEBAR ---
st.sidebar.header("📂 Data Source")
uploaded_file = st.sidebar.file_uploader("Upload JSON or JSONL", type=["json", "jsonl"])

raw_json = None

if uploaded_file is not None:
    try:
        raw_json = load_json_or_jsonl(uploaded_file)
        st.sidebar.success(f"Loaded: {uploaded_file.name}")
        st.sidebar.info(f"Total Records: {len(raw_json)}")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
else:
    st.sidebar.info("Using embedded demo data.")
    raw_json = json.loads(DEMO_JSON_DATA)

if not HAS_LANGDETECT:
    st.sidebar.warning("⚠️ `langdetect` not installed. Language detection disabled.")

# --- PROCESS DATA ---
if raw_json:
    if not isinstance(raw_json, list):
        st.error("Invalid data format.")
        st.stop()
    data, available_themes, available_axes, available_others, available_langs, available_lengths = process_data(raw_json)
else:
    st.stop()

# --- FILTERS ---
st.sidebar.header("🔍 Filters")
selected_themes = st.sidebar.multiselect("Theme", available_themes, default=available_themes)

if HAS_LANGDETECT and len(available_langs) > 0:
    selected_langs = st.sidebar.multiselect("Language", available_langs, default=available_langs)
else:
    selected_langs = available_langs

# Conversation Length Filter
selected_lengths = st.sidebar.multiselect("Conversation Length", available_lengths, default=available_lengths)

selected_axes = st.sidebar.multiselect("Axis (Rubric)", available_axes)
selected_others = st.sidebar.multiselect("Category/Tag", available_others)

# --- FILTER LOGIC ---
filtered_data = []
for item in data:
    meta = item['processed_meta']
    has_theme = not selected_themes or any(t in selected_themes for t in meta['themes'])
    has_axis = not selected_axes or any(a in selected_axes for a in meta['axes'])
    has_other = not selected_others or any(o in selected_others for o in meta['others'])
    has_length = not selected_lengths or meta['turn_category'] in selected_lengths
    
    has_lang = True
    if HAS_LANGDETECT:
        has_lang = not selected_langs or meta['language'] in selected_langs
    
    if has_theme and has_axis and has_other and has_lang and has_length:
        filtered_data.append(item)

st.sidebar.markdown("---")
st.sidebar.write(f"**Samples Matched:** {len(filtered_data)}")

if not filtered_data:
    st.warning("No samples match your filters.")
    st.stop()

# --- TABS ---
active_themes_in_data = set()
for item in filtered_data:
    active_themes_in_data.update(item['processed_meta']['themes'])

tabs_to_create = [t for t in selected_themes if t in active_themes_in_data]
if not tabs_to_create:
    tabs_to_create = ["Uncategorized/Other"]

tabs = st.tabs(tabs_to_create)

for tab, theme_name in zip(tabs, tabs_to_create):
    with tab:
        # Get data for this specific theme
        if theme_name == "Uncategorized/Other":
            tab_samples = filtered_data
        else:
            tab_samples = [d for d in filtered_data if theme_name in d['processed_meta']['themes']]
        
        if not tab_samples:
            st.write("No samples.")
            continue
            
        count = len(tab_samples)

        # --- NAVIGATION (SLIDER RESTORED) ---
        col_info, col_slider = st.columns([1, 4])
        with col_info:
            st.write(f"**Total Samples:** {count}")
        
        sample_index = 0
        if count > 1:
            # We use a unique key per theme so sliders don't conflict
            sample_index = st.slider(
                f"Select Sample ({theme_name})", 
                0, 
                count - 1, 
                0, 
                key=f"slider_{theme_name}"
            )

        sample = tab_samples[sample_index]
        
        # --- DISPLAY CONTENT ---
        st.divider()
        lang_badge = f"mapped lang: `{sample['processed_meta']['language']}`" if HAS_LANGDETECT else ""
        turn_badge = f"turns: `{sample['processed_meta']['turn_count']}`"
        
        st.markdown(f"### 🆔 `{sample.get('prompt_id', 'N/A')}` {lang_badge} {turn_badge}")
        
        all_tags = sample.get("example_tags", [])
        st.markdown("**Tags:** " + " ".join([f"`{t}`" for t in all_tags]))

        col_chat, col_rubric = st.columns([1, 1])

        # LEFT: Chat
        with col_chat:
            st.subheader("💬 Context")
            chat_container = st.container(border=True)
            with chat_container:
                for msg in sample.get("prompt", []):
                    role = msg.get("role", "unknown").lower()
                    content = msg.get("content", "")
                    avatar = "👤" if role == "user" else "🤖"
                    with st.chat_message(role, avatar=avatar):
                        st.markdown(content)

            ideal = sample.get("ideal_completions_data")
            if ideal:
                with st.expander("✨ Ideal Completion"):
                    if isinstance(ideal, dict) and "ideal_completion" in ideal:
                        st.info(ideal["ideal_completion"])
                    elif isinstance(ideal, list):
                        st.info(ideal[0])
                    else:
                        st.write(ideal)

        # RIGHT: Rubric
        with col_rubric:
            st.subheader("✅ Rubric")
            rubrics = sample.get("rubrics", [])
            if rubrics:
                rubric_data = []
                for r in rubrics:
                    r_tags = r.get("tags", [])
                    axis_tag = next((t.split(":", 1)[1] for t in r_tags if t.startswith("axis:")), "General")
                    rubric_data.append({
                        "Points": r.get("points", 0),
                        "Axis": axis_tag,
                        "Criterion": r.get("criterion", ""),
                    })
                
                df = pd.DataFrame(rubric_data)
                st.dataframe(
                    df.style.map(color_points, subset=["Points"]),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Criterion": st.column_config.TextColumn("Criterion", width="large"),
                        "Points": st.column_config.NumberColumn("Pts", format="%d"),
                        "Axis": st.column_config.TextColumn("Axis", width="small"),
                    }
                )
            else:
                st.warning("No rubrics found.")
