import time
from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.thread_message import ThreadMessage
from openai.types.beta.threads.run import Run
import json
import streamlit as st
from financial_functions import get_income_statement, get_balance_sheet_statement, get_cash_flow_statement, get_cash_flow_statement_growth, get_financial_ratios, get_key_metrics
from create_assistant import create_assistant

st.set_page_config(
    page_title="The Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

FMP_API_KEY = st.secrets["FMP_API_KEY"]
st.sidebar.title("Assistants API")

available_functions = {
    "get_income_statement": get_income_statement,
    "get_balance_sheet_statement": get_balance_sheet_statement,
    "get_cash_flow_statement": get_cash_flow_statement,
    "get_cash_flow_statement_growth": get_cash_flow_statement_growth,
    "get_financial_ratios": get_financial_ratios,
    "get_key_metrics": get_key_metrics,
}

if "client" not in st.session_state:
     st.session_state.client = OpenAI()

assistansList = st.session_state.client.beta.assistants.list()

if "Financial Analyst" not in [m.name for m in assistansList.data]:
    create_assistant(client=st.session_state.client)
    assistansList = st.session_state.client.beta.assistants.list()

assistantName = st.sidebar.selectbox("Available Assistants",[m.name for m in assistansList.data])
assistant: Assistant = next((m for m in assistansList.data if m.name == assistantName),None)

st.session_state["openai_model"] = assistant.model
st.subheader(assistant.name)


if "messages" not in st.session_state:
    st.session_state.messages = []

prompt = st.chat_input("Say something")

if prompt:
    
    #Step 2: Create a Thread
    if "thread" not in st.session_state:
        st.session_state.thread: Thread  = st.session_state.client.beta.threads.create()

    #Step 3: Add a Message to a Thread
    message = st.session_state.client.beta.threads.messages.create(
        thread_id=st.session_state.thread.id,
        role="user",
        content=prompt
    )   

    #Step 4: Run the Assistant
    run: Run = st.session_state.client.beta.threads.runs.create(
    thread_id=st.session_state.thread.id,
    assistant_id=assistant.id,
    instructions="Please address the user as Hannan. The user has a premium account."
    )

    #Step 5: Check the Run status
    with st.status("Generating Response...", expanded=False) as status:
        while True:
            run = st.session_state.client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread.id,
                    run_id=run.id,
                )
            st.write(run.status)
            if run.status == "queued" or run.status == "in_progress":
                time.sleep(5)

            elif run.status == "requires_action":
                if run.required_action.submit_tool_outputs and run.required_action.submit_tool_outputs.tool_calls:
                    tools_outputs = []
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    for toolCall in tool_calls:
                        function_name = toolCall.function.name
                        function_args = json.loads(toolCall.function.arguments)
                        if function_name in available_functions:
                            function_to_call = available_functions[function_name]
                            response = function_to_call(**function_args)
                            tools_outputs.append(
                                {
                                    "tool_call_id":toolCall.id,
                                    "output": response
                                }
                            )
                    st.session_state.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=st.session_state.thread.id,
                        run_id=run.id,
                        tool_outputs=tools_outputs
                    )
                
            elif run.status == "completed":
                status.update(label="Download complete!", state="complete", expanded=False)
                break
            elif run.status == "failed":
                st.error(run.status)
                break
            else:
                st.info(f"Unexpected status: {run.status}")
                break

    #Step 6: Display the Assistant's Response

    messages: list[ThreadMessage] = st.session_state.client.beta.threads.messages.list(
    thread_id=st.session_state.thread.id
    )

    st.session_state.messages = [msg for msg in reversed(messages.data)]

    for message in st.session_state.messages:
        with st.chat_message(message.role):
            for mc in message.content:
                if mc.type == "text":
                    st.markdown(mc.text.value)
                if mc.type == "image_file":
                    fileid = (mc.image_file.file_id)
                    image_data = st.session_state.client.files.content(file_id=fileid)
                    image_data_bytes = image_data.read()
                    with open(f"""./{fileid}.png""", "wb") as file:
                        file.write(image_data_bytes)
                        st.image(f"""./{fileid}.png""")