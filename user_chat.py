#user_chat.py

import requests
import streamlit as st

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

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! To get started, tell me about your business."}
    ]

def handle_user_input(prompt):
    if st.session_state.session_id is None:
        st.error("Session ID is not set. Please ask the admin to upload the relevant documents.")
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    response = send_to_api('ask', data={"session_id": st.session_state.session_id, "query": prompt})

    if response and "response" in response:
        response_text = response["response"]
        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Handling response based on content
        if "category" in response_text.lower():
            st.session_state.messages.append({"role": "assistant", "content": "Please select a template from the options provided."})
        elif "template" in response_text.lower():
            st.session_state.messages.append({"role": "assistant", "content": "Would you like to add more pages? Please provide the details."})
        elif "pages" in response_text.lower():
            st.session_state.messages.append({"role": "assistant", "content": "Your choices have been saved. You can now customize your pages in the LCNC platform."})
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

