import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import uuid
from datetime import datetime
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_openai import ChatOpenAI
import os
# api_key = os.getenv("GEMINI_API_KEY")
load_dotenv()
# model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

model = ChatOpenAI()

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

def get_session_history(user_id: str, conversation_id: str) -> ChatMessageHistory:
    if (user_id, conversation_id) not in st.session_state.store:
        st.session_state.store[(user_id, conversation_id)] = ChatMessageHistory()
    return st.session_state.store[(user_id, conversation_id)]

def create_new_conversation():
    st.session_state.conversation_counter+=1
    new_conv_id = str(uuid.uuid4())
    st.session_state.conversations[new_conv_id] = {
        "number": st.session_state.conversation_counter,
        "messages": []
    }
    st.session_state.current_conversation_id = new_conv_id

prompt = ChatPromptTemplate(
    [
        (
            "system",
            "You are a helpful. Answer all questions to the best of your ability.",
        )
    ,
    MessagesPlaceholder(variable_name="mychat_history"),
    (
        "human",
        "{myinput}"
    )
    ]
)

chain = prompt | model

model_with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history, 
    input_messages_key="myinput",
    history_messages_key="mychat_history",
    history_factory_config=[
        ConfigurableFieldSpec(
            id="user_id",
            annotation=str,
            name="User ID"
        ),
        ConfigurableFieldSpec(
            id="conversation_id",
            annotation=str,
            name="Conversation ID"
        )
    ]
)

st.title("Jarvis")

with st.sidebar:
    st.subheader("Conversations")

    if st.button("New Conversations", key="new_conv"):
        create_new_conversation()
    
    conversations_list = [
        (
            conv_id, 
            f"Conversation {conv_data['number']}"
        )

        for conv_id, conv_data in st.session_state.conversations.items()
    ]

    selected_conv = st.selectbox(
    "Select Conversation",
    options=[conv[0] for conv in conversations_list],
    index=list(st.session_state.conversations.keys()).index(st.session_state.current_conversation_id))


    if selected_conv!=st.session_state.current_conversation_id:
        st.session_state.current_conversation_id = selected_conv

    st.sidebar.divider()
    st.sidebar.write(f"Current User ID: {st.session_state.user_id}")
    st.sidebar.write(f"Current Conversation ID: {st.session_state.current_conversation_id}")

prompt = st.chat_input("What's on your mind?")
if prompt:
    current_conv=st.session_state.conversations[st.session_state.current_conversation_id]
    current_conv['messages'].append(
        {
            'role': 'user',
            'content': prompt,
        }
    )

    config = {"configurable": {"user_id": st.session_state.user_id, 
                               "conversation_id": st.session_state.current_conversation_id}}
    response = model_with_message_history.invoke(
        input={"myinput": prompt},
        config= config
    )


    current_conv['messages'].append(
        {
            'role': 'assistant',
            'content': response.content,
        }
    )
current_conv=st.session_state.conversations[st.session_state.current_conversation_id]

for message in current_conv['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])