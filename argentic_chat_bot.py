import streamlit as st
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai

# Load environment variables
# Default to None
GEMINI_API_KEY = None

# Use secrets in deployment
# Load .env file (LOCAL DEVELOPMENT)
if os.path.exists(".env"):
    load_dotenv()  # Load environment variables
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Use Streamlit Secrets (DEPLOYMENT)
elif "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=os.getenv(GEMINI_API_KEY))

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Session state initialization
if "store" not in st.session_state:
    st.session_state.store = {}

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "conversation_counter" not in st.session_state:
    st.session_state.conversation_counter = 1

if "current_conversation_id" not in st.session_state:
    new_conv_id = str(uuid.uuid4())
    st.session_state.conversations[new_conv_id] = {
        "number": st.session_state.conversation_counter,
        "messages": []
    }
    st.session_state.current_conversation_id = new_conv_id

# Function to create a new conversation
def create_new_conversation():
    st.session_state.conversation_counter += 1
    new_conv_id = str(uuid.uuid4())
    st.session_state.conversations[new_conv_id] = {
        "number": st.session_state.conversation_counter,
        "messages": []
    }
    st.session_state.current_conversation_id = new_conv_id

# Function to get Gemini response
def get_model_response(history, user_input):
    chat_history = [{"role": msg["role"], "parts": [msg["content"]]} for msg in history]
    chat_history.append({"role": "user", "parts": [user_input]})
    
    convo = model.start_chat(history=chat_history)
    response = convo.send_message(user_input)
    return response.text

# UI
st.title("Jarvis")

# Sidebar for conversation management
with st.sidebar:
    st.subheader("Conversations")

    if st.button("New Conversation", key="new_conv"):
        create_new_conversation()

    conversations_list = [
        (conv_id, f"Conversation {conv_data['number']}")
        for conv_id, conv_data in st.session_state.conversations.items()
    ]

    selected_conv = st.selectbox(
        "Select Conversation",
        options=[conv[0] for conv in conversations_list],
        format_func=lambda x: dict(conversations_list)[x],
        index=list(st.session_state.conversations.keys()).index(st.session_state.current_conversation_id)
    )

    if selected_conv != st.session_state.current_conversation_id:
        st.session_state.current_conversation_id = selected_conv

    st.sidebar.divider()
    st.sidebar.write(f"Current User ID: {st.session_state.user_id}")
    st.sidebar.write(f"Current Conversation ID: {st.session_state.current_conversation_id}")

# Main chat input and logic
prompt = st.chat_input("What's on your mind?")
if prompt:
    current_conv = st.session_state.conversations[st.session_state.current_conversation_id]

    # Append user's message
    current_conv['messages'].append({
        'role': 'user',
        'content': prompt,
    })

    # Get response from Gemini
    response_text = get_model_response(current_conv['messages'], prompt)

    # Append assistant's response
    current_conv['messages'].append({
        'role': 'assistant',
        'content': response_text,
    })

# Render chat history
current_conv = st.session_state.conversations[st.session_state.current_conversation_id]
for message in current_conv['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
