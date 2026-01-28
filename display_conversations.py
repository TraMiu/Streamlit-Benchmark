# import streamlit as st
# import json

# def main():
#     st.set_page_config(page_title="Veterinary Q&A Editor", layout="wide")

#     # --- 1. Session State Initialization ---
#     if 'data' not in st.session_state:
#         st.session_state['data'] = []
#     if 'file_loaded' not in st.session_state:
#         st.session_state['file_loaded'] = False

#     # --- 2. Sidebar: File Upload & Export ---
#     st.sidebar.title("📂 Data Management")
#     uploaded_file = st.sidebar.file_uploader("Upload JSON", type=["json"])

#     if uploaded_file is not None and not st.session_state['file_loaded']:
#         try:
#             raw_data = json.load(uploaded_file)
#             if isinstance(raw_data, list):
#                 st.session_state['data'] = raw_data
#                 st.session_state['file_loaded'] = True
#                 st.rerun()
#             else:
#                 st.error("JSON root must be a list.")
#         except Exception as e:
#             st.error(f"Error reading file: {e}")

#     # Reset & Download
#     if st.session_state['file_loaded']:
#         if st.sidebar.button("🔄 Reset / Upload New File"):
#             st.session_state['data'] = []
#             st.session_state['file_loaded'] = False
#             st.rerun()
        
#         st.sidebar.markdown("---")
#         st.sidebar.subheader("💾 Save Your Work")
        
#         # Download logic
#         json_str = json.dumps(st.session_state['data'], indent=4)
#         st.sidebar.download_button(
#             label="Download Modified JSON",
#             data=json_str,
#             file_name="veterinary_data_reviewed.json",
#             mime="application/json"
#         )

#     # --- 3. Main Interface ---
#     if st.session_state['file_loaded']:
#         data = st.session_state['data']
        
#         # Group by Topic
#         grouped_data = {}
#         for idx, item in enumerate(data):
#             topic = item.get('topic', 'Uncategorized') or 'Uncategorized'
#             if topic not in grouped_data:
#                 grouped_data[topic] = []
#             grouped_data[topic].append({'original_index': idx, 'content': item})

#         sorted_topics = sorted(grouped_data.keys())
#         tabs = st.tabs(sorted_topics)

#         for i, topic in enumerate(sorted_topics):
#             with tabs[i]:
#                 topic_items = grouped_data[topic]
                
#                 # Selector
#                 options = [
#                     f"{item['content'].get('number', 'N/A')} - {item['content'].get('question', '')[:60]}..." 
#                     for item in topic_items
#                 ]
                
#                 selected_idx_in_group = st.selectbox(
#                     f"Select Record in '{topic}'", 
#                     range(len(topic_items)),
#                     format_func=lambda x: options[x],
#                     key=f"select_{topic}"
#                 )

#                 # Retrieve Record
#                 current_record_map = topic_items[selected_idx_in_group]
#                 original_index = current_record_map['original_index']
#                 record = st.session_state['data'][original_index]

#                 st.markdown("---")

#                 # --- TOP SECTION: Static Reference Info ---
#                 with st.expander("❓ View Reference Context (Question, Answer, Notes)", expanded=False):
#                     c1, c2 = st.columns(2)
#                     with c1:
#                         st.markdown("**Question:**")
#                         st.info(record.get('question', 'N/A'))
#                         st.markdown("**Gold Answer:**")
#                         st.success(record.get('answer', 'N/A'))
#                     with c2:
#                         st.markdown("**Veterinary Notes:**")
#                         st.markdown(record.get('notes', 'No notes.'))

#                 # --- BOTTOM SECTION: Conversation Editor ---
#                 st.subheader("💬 Conversation Editor")
#                 st.caption("Edit the dialogue on the left. Add comments for specific turns on the right.")

#                 prompts = record.get('prompt', [])
                
#                 if not prompts:
#                     st.warning("No conversation turns found.")
                
#                 # Loop through every turn in the conversation
#                 for p_idx, msg in enumerate(prompts):
#                     role = msg.get('role', 'user')
#                     content = msg.get('content', '')
#                     # Get existing comment for this specific turn, if any
#                     turn_comment = msg.get('reviewer_comment', '')

#                     # Styling based on role
#                     if role == 'user':
#                         emoji = "🧑‍🌾"
#                         role_label = "User"
#                         color = "blue"
#                     else:
#                         emoji = "🩺"
#                         role_label = "Assistant"
#                         color = "green"

#                     with st.container(border=True):
#                         # Header for the turn
#                         st.markdown(f":{color}[**{emoji} {role_label} (Turn {p_idx+1})**]")
                        
#                         c_text, c_comment = st.columns([0.7, 0.3])
                        
#                         # LEFT: The Conversation Text
#                         with c_text:
#                             new_text = st.text_area(
#                                 "Content",
#                                 value=content,
#                                 height=100,
#                                 label_visibility="collapsed",
#                                 key=f"text_{original_index}_{p_idx}"
#                             )
#                             # Update Text
#                             if new_text != content:
#                                 st.session_state['data'][original_index]['prompt'][p_idx]['content'] = new_text

#                         # RIGHT: The Comment for this turn
#                         with c_comment:
#                             new_comment = st.text_area(
#                                 "📝 Comment",
#                                 value=turn_comment,
#                                 height=100,
#                                 placeholder="Add feedback for this turn...",
#                                 label_visibility="collapsed",
#                                 key=f"comment_{original_index}_{p_idx}"
#                             )
#                             # Update Comment
#                             if new_comment != turn_comment:
#                                 st.session_state['data'][original_index]['prompt'][p_idx]['reviewer_comment'] = new_comment

#     else:
#         st.info("👆 Please upload a JSON file to start editing.")

# if __name__ == "__main__":
#     main()

import streamlit as st
import json

def main():
    st.set_page_config(page_title="Veterinary Q&A Editor", layout="wide")

    # --- 1. Session State Initialization ---
    if 'data' not in st.session_state:
        st.session_state['data'] = []
    if 'file_loaded' not in st.session_state:
        st.session_state['file_loaded'] = False

    # --- 2. Sidebar: File Upload & Export ---
    st.sidebar.title("📂 Data Management")
    uploaded_file = st.sidebar.file_uploader("Upload JSON", type=["json"])

    if uploaded_file is not None and not st.session_state['file_loaded']:
        try:
            raw_data = json.load(uploaded_file)
            if isinstance(raw_data, list):
                # Ensure every record has a status key, defaulting to Unapproved
                for item in raw_data:
                    if 'status' not in item:
                        item['status'] = 'Unapproved'
                
                st.session_state['data'] = raw_data
                st.session_state['file_loaded'] = True
                st.rerun()
            else:
                st.error("JSON root must be a list.")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    # Reset & Download
    if st.session_state['file_loaded']:
        if st.sidebar.button("🔄 Reset / Upload New File"):
            st.session_state['data'] = []
            st.session_state['file_loaded'] = False
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("💾 Save Your Work")
        
        # Download logic
        json_str = json.dumps(st.session_state['data'], indent=4)
        st.sidebar.download_button(
            label="Download Modified JSON",
            data=json_str,
            file_name="veterinary_data_reviewed.json",
            mime="application/json"
        )

    # --- 3. Main Interface ---
    if st.session_state['file_loaded']:
        data = st.session_state['data']
        
        # Group by Topic
        grouped_data = {}
        for idx, item in enumerate(data):
            topic = item.get('topic', 'Uncategorized') or 'Uncategorized'
            if topic not in grouped_data:
                grouped_data[topic] = []
            grouped_data[topic].append({'original_index': idx, 'content': item})

        sorted_topics = sorted(grouped_data.keys())
        tabs = st.tabs(sorted_topics)

        for i, topic in enumerate(sorted_topics):
            with tabs[i]:
                topic_items = grouped_data[topic]
                
                # Selector
                # Display status icon in the dropdown options
                options = []
                for item in topic_items:
                    status_icon = "✅" if item['content'].get('status') == "Approved" else "⚠️"
                    q_text = item['content'].get('question', '')[:50]
                    rec_id = item['content'].get('number', 'N/A')
                    options.append(f"{status_icon} [{rec_id}] {q_text}...")
                
                selected_idx_in_group = st.selectbox(
                    f"Select Record in '{topic}'", 
                    range(len(topic_items)),
                    format_func=lambda x: options[x],
                    key=f"select_{topic}"
                )

                # Retrieve Record
                current_record_map = topic_items[selected_idx_in_group]
                original_index = current_record_map['original_index']
                record = st.session_state['data'][original_index]

                st.markdown("---")

                # --- HEADER: Status Toggle & Metadata ---
                # We put this in a container to make it prominent
                with st.container(border=True):
                    col_status, col_meta = st.columns([0.4, 0.6])
                    
                    with col_status:
                        st.caption("Review Status")
                        current_status = record.get('status', 'Unapproved')
                        
                        # Status Toggle
                        new_status = st.radio(
                            "Status",
                            options=["Unapproved", "Approved"],
                            index=0 if current_status == "Unapproved" else 1,
                            horizontal=True,
                            label_visibility="collapsed",
                            key=f"status_toggle_{original_index}"
                        )

                        # Update State if changed
                        if new_status != current_status:
                            st.session_state['data'][original_index]['status'] = new_status
                            st.rerun() # Rerun to update the dropdown icon immediately

                        # Visual Feedback
                        if new_status == "Approved":
                            st.success("✅ This record is marked as **APPROVED**")
                        else:
                            st.warning("⚠️ This record is **UNAPPROVED**")

                    with col_meta:
                        st.caption("Record Details")
                        st.text(f"ID: {record.get('number', 'N/A')}")
                        st.text(f"Topic: {topic}")


                # --- MIDDLE: Static Reference Info ---
                with st.expander("❓ View Reference Context (Question, Answer, Notes)", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Question:**")
                        st.info(record.get('question', 'N/A'))
                        st.markdown("**Gold Answer:**")
                        st.success(record.get('answer', 'N/A'))
                    with c2:
                        st.markdown("**Veterinary Notes:**")
                        st.markdown(record.get('notes', 'No notes.'))

                # --- BOTTOM: Conversation Editor ---
                st.subheader("💬 Conversation Editor")
                st.caption("Edit the dialogue on the left. Add comments for specific turns on the right.")

                prompts = record.get('prompt', [])
                
                if not prompts:
                    st.warning("No conversation turns found.")
                
                # Loop through every turn in the conversation
                for p_idx, msg in enumerate(prompts):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    turn_comment = msg.get('reviewer_comment', '')

                    # Styling based on role
                    if role == 'user':
                        emoji = "🧑‍🌾"
                        role_label = "User"
                        color = "blue"
                    else:
                        emoji = "🩺"
                        role_label = "Assistant"
                        color = "green"

                    with st.container(border=True):
                        # Header for the turn
                        st.markdown(f":{color}[**{emoji} {role_label} (Turn {p_idx+1})**]")
                        
                        c_text, c_comment = st.columns([0.7, 0.3])
                        
                        # LEFT: The Conversation Text
                        with c_text:
                            new_text = st.text_area(
                                "Content",
                                value=content,
                                height=100,
                                label_visibility="collapsed",
                                key=f"text_{original_index}_{p_idx}"
                            )
                            if new_text != content:
                                st.session_state['data'][original_index]['prompt'][p_idx]['content'] = new_text

                        # RIGHT: The Comment for this turn
                        with c_comment:
                            new_comment = st.text_area(
                                "📝 Comment",
                                value=turn_comment,
                                height=100,
                                placeholder="Add feedback for this turn...",
                                label_visibility="collapsed",
                                key=f"comment_{original_index}_{p_idx}"
                            )
                            if new_comment != turn_comment:
                                st.session_state['data'][original_index]['prompt'][p_idx]['reviewer_comment'] = new_comment

    else:
        st.info("👆 Please upload a JSON file to start editing.")

if __name__ == "__main__":
    main()
