#!/usr/bin/env python
# coding: utf-8

# In[4]:


import os, sys
import streamlit as st
from datetime import datetime
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Add current directory to Python path so local modules can be imported
sys.path.append(os.getcwd())

# Import your custom tool to log time to Jira Tempo
from timesheet_tool import LogTimeToTempoTool

# Initialize the language model with Gemini 2.5 Flash variant and moderate temperature for response variability
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

# Initialize the time-logging tool with credentials and Jira domain read from environment variables
tool_instance = LogTimeToTempoTool(
    jira_email=os.environ.get("JIRA_EMAIL"),
    jira_token=os.environ.get("JIRA_TOKEN"),
    tempo_token=os.environ.get("TEMPO_TOKEN"),
    jira_domain=os.environ.get("JIRA_DOMAIN").rstrip('/')
)
tools = [tool_instance]

# Create an agent that binds the LLM with the tools for reactive interaction
agent_executor = create_react_agent(model, tools)

# Streamlit UI setup: page title and layout
st.set_page_config(page_title="Jira Time Tracker", layout="centered")
st.title("Jira Time-Tracking Assistant")

# Input textarea for user to type their time log commands or requests
user_input = st.text_area("What would you like to log?", height=100,
                          placeholder="e.g. Log 7.5 hours to all in-progress issues for this full week.")


# Button triggers the logging process if user input is not empty
if st.button("Log Time") and user_input.strip():
    with st.spinner("Thinking..."):
        # Prepare the conversation messages to provide context and user input
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a time-tracking assistant that updates Jira issues using provided tools. "
                    "If the user does not specify an issue key, assume the issue key is 'MGAP-X'. "
                    "Do not ask the user for clarification or confirmation — just proceed with the default value. "
                    "Only respond with the result or tool call."
                )
            },
            {"role": "user", "content": user_input}
        ]

        try:
            # Invoke the agent with the prepared messages and get response
            response = agent_executor.invoke({"messages": messages})

            # Process and display assistant messages returned by the agent
            if "messages" in response:
                for msg in response["messages"]:
                    if isinstance(msg, BaseMessage):
                        st.write(f"[{msg.type.upper()}] {msg.content}")

                        # Special handling for tool messages
                        if msg.type == "tool":
                            # Handle tool message
                            st.write(f"Tool message from: {getattr(msg, 'name', 'unknown')} — {msg.content}")

                        # Handling AI messages which may include tool calls or plain text response
                        elif msg.type == "ai":
                            # Might have tool_calls or response text
                            tool_calls = getattr(msg, "tool_calls", [])
                            if tool_calls:
                                st.write(f"Tool calls: {tool_calls}")
                            else:
                                st.write(f"Final AI Response: {msg.content}")
            else:
                # Warn user if no messages are returned from the agent
                st.warning("No messages returned.")

        except Exception as e:
            # Show exception details in the Streamlit app UI for debugging
            st.exception(e)


# In[ ]:




