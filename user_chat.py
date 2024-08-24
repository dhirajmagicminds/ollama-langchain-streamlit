# user_chat.py

import requests
import streamlit as st
import uuid

API_URL = "http://middle_layer:8000"

def send_to_api(endpoint, data=None):
    try:
        response = requests.post(f"{API_URL}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

st.set_page_config(page_title="LCNC Guide Chat", page_icon=":robot:")
st.title("LCNC Guide Chat")

# Initialize session states
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())  # Automatically generate session ID for the user

if "business_category" not in st.session_state:
    st.session_state.business_category = None

if "template_selected" not in st.session_state:
    st.session_state.template_selected = None

if "pages_selected" not in st.session_state:
    st.session_state.pages_selected = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! Let's get started. Tell me about your business?"}
    ]

def handle_user_input(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Determine conversation flow based on current state
    if st.session_state.business_category is None:
        st.session_state.business_category = prompt
        st.session_state.messages.append({"role": "assistant", "content": "Great! Please select a template that fits your business."})
    elif st.session_state.template_selected is None:
        st.session_state.template_selected = prompt
        st.session_state.messages.append({"role": "assistant", "content": "Would you like to add more pages? Please provide the page details."})
    elif st.session_state.pages_selected is None:
        st.session_state.pages_selected = prompt
        st.session_state.messages.append({"role": "assistant", "content": "Your choices have been saved. You can now customize your pages in the LCNC platform."})
    else:
        # If all initial information is gathered, proceed with normal Q&A
        response = send_to_api('ask', data={"session_id": st.session_state.session_id, "query": prompt})
        if response and "response" in response:
            st.session_state.messages.append({"role": "assistant", "content": response["response"]})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "I didn't get that. Can you please provide more details?"})

# Chat input handling
prompt = st.chat_input("Your question")
if prompt:
    handle_user_input(prompt)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
