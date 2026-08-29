import streamlit as st
import urllib.request
import urllib.error
import json
import ast
import operator
from datetime import datetime


APP_NAME = "X AI"
MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"


st.set_page_config(
    page_title="X AI",
    page_icon="X",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #080b10;
    color: #f5f7fa;
}

section[data-testid="stSidebar"] {
    background-color: #10151c;
}

.sidebar-x {
    font-size: 64px;
    font-weight: 900;
    text-align: center;
    color: white;
    margin-top: 10px;
}

.sidebar-subtitle {
    text-align: center;
    color: #9ba3af;
    font-size: 14px;
    margin-bottom: 25px;
}

.welcome-box {
    background-color: #10151c;
    border: 1px solid #293342;
    border-radius: 18px;
    padding: 45px;
    text-align: center;
    margin-bottom: 30px;
}

.big-x {
    font-size: 72px;
    font-weight: 900;
    color: white;
}

.welcome-title {
    font-size: 30px;
    font-weight: 700;
    color: white;
}

.welcome-text {
    color: #9ba3af;
    font-size: 16px;
    line-height: 1.7;
}

.quick-title {
    font-size: 23px;
    font-weight: 700;
    color: white;
    margin-bottom: 15px;
}

.user-box {
    background-color: #18202a;
    border: 1px solid #293342;
    border-radius: 14px;
    padding: 15px;
    margin: 10px 0;
}

.ai-box {
    background-color: #10151c;
    border: 1px solid #293342;
    border-radius: 14px;
    padding: 15px;
    margin: 10px 0 20px 0;
}

.label {
    color: #9ba3af;
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 7px;
}

.stButton > button {
    background-color: #151c25;
    color: white;
    border: 1px solid #303a48;
    border-radius: 10px;
    min-height: 42px;
}

.stButton > button:hover {
    border-color: #657185;
    color: white;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "chats" not in st.session_state:
    st.session_state.chats = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


# ============================================================
# CHAT FUNCTIONS
# ============================================================

def create_new_chat():

    number = len(st.session_state.chats) + 1

    chat = {
        "name": "New Chat " + str(number),
        "messages": []
    }

    st.session_state.chats.append(chat)

    st.session_state.current_chat = (
        len(st.session_state.chats) - 1
    )


def get_current_chat():

    if st.session_state.current_chat is None:
        return None

    index = st.session_state.current_chat

    if index < 0:
        return None

    if index >= len(st.session_state.chats):
        return None

    return st.session_state.chats[index]


def delete_chat(index):

    if index < 0:
        return

    if index >= len(st.session_state.chats):
        return

    st.session_state.chats.pop(index)

    if len(st.session_state.chats) == 0:

        st.session_state.current_chat = None

    elif st.session_state.current_chat >= len(
        st.session_state.chats
    ):

        st.session_state.current_chat = (
            len(st.session_state.chats) - 1
        )


def rename_chat(chat, message):

    if len(chat["messages"]) != 1:
        return

    name = message.strip()

    if len(name) > 28:
        name = name[:28] + "..."

    chat["name"] = name


# ============================================================
# CALCULATOR
# ============================================================

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos
}


def safe_calculate(expression):

    tree = ast.parse(
        expression.strip(),
        mode="eval"
    )

    def calculate(node):

        if isinstance(node, ast.Expression):
            return calculate(node.body)

        if isinstance(node, ast.Constant):

            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError()

        if isinstance(node, ast.BinOp):

            left = calculate(node.left)
            right = calculate(node.right)

            operation = OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError()

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):

            value = calculate(node.operand)

            operation = OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError()

            return operation(value)

        raise ValueError()

    return calculate(tree)


# ============================================================
# LOCAL COMMANDS
# ============================================================

def local_command(message):

    text = message.strip()
    lower = text.lower()


    if lower in [
        "/time",
        "time",
        "current time",
        "what is the time"
    ]:

        return (
            "The current local time is "
            + datetime.now().strftime(
                "%I:%M:%S %p"
            )
        )


    if lower in [
        "/date",
        "date",
        "today",
        "what is today's date"
    ]:

        return (
            "Today's date is "
            + datetime.now().strftime(
                "%d %B %Y"
            )
        )


    if lower.startswith("/calc "):

        expression = text[6:]

        try:

            answer = safe_calculate(
                expression
            )

            return "Answer: " + str(answer)

        except Exception:

            return (
                "I couldn't calculate that.\n\n"
                "Example: /calc 25*4+10"
            )


    if lower in ["/help", "help"]:

        return (
            "X AI Commands\n\n"
            "/time - current time\n\n"
            "/date - today's date\n\n"
            "/calc 25*4+10 - calculator\n\n"
            "You can also ask normal questions."
        )


    return None


# ============================================================
# OLLAMA
# ============================================================

def ask_ollama(messages):

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    data = json.dumps(payload).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )


    try:

        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            result = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )


        if "message" in result:

            if "content" in result["message"]:

                return result["message"]["content"]


        if "error" in result:

            return (
                "Ollama error: "
                + str(result["error"])
            )


        return (
            "X AI received an unexpected "
            "response from Ollama."
        )


    except urllib.error.URLError:

        return (
            "I cannot connect to Ollama.\n\n"
            "Make sure Ollama is running and "
            "the model "
            + MODEL
            + " is installed."
        )


    except Exception as error:

        return (
            "X AI connection error: "
            + str(error)
        )


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are X AI.

You are a helpful personal AI assistant.

Help the user with:

Programming
Python
C
HTML
CSS
JavaScript
AutoCAD
Mathematics
Science
English
Study topics
General questions

Explain difficult topics simply.

Give complete working code when code is requested.

Be friendly, useful and concise.

Do not pretend that you have internet access.
"""


# ============================================================
# ASK X
# ============================================================

def ask_x(message):

    chat = get_current_chat()


    if chat is None:

        create_new_chat()

        chat = get_current_chat()


    chat["messages"].append(
        {
            "role": "user",
            "content": message
        }
    )


    rename_chat(
        chat,
        message
    )


    answer = local_command(
        message
    )


    if answer is not None:

        chat["messages"].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return


    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


    for item in chat["messages"]:

        messages.append(
            {
                "role": item["role"],
                "content": item["content"]
            }
        )


    answer = ask_ollama(
        messages
    )


    chat["messages"].append(
        {
            "role": "assistant",
            "content": answer
        }
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # Normal Streamlit text.
    # No HTML is used for the logo.
    st.markdown(
        "## X"
    )

    st.caption(
        "Personal Local AI"
    )


    if st.button(
        "+ New Chat",
        use_container_width=True
    ):

        create_new_chat()

        st.rerun()


    st.divider()

    st.markdown(
        "### Chats"
    )


    if len(st.session_state.chats) == 0:

        st.caption(
            "No chats yet."
        )


    else:

        for index, item in enumerate(
            st.session_state.chats
        ):

            col1, col2 = st.columns(
                [5, 1]
            )


            with col1:

                if st.button(
                    item["name"],
                    key="chat_" + str(index),
                    use_container_width=True
                ):

                    st.session_state.current_chat = index

                    st.rerun()


            with col2:

                if st.button(
                    "X",
                    key="delete_" + str(index)
                ):

                    delete_chat(index)

                    st.rerun()


    st.divider()

    st.markdown(
        "### X AI"
    )

    st.caption(
        "Model: " + MODEL
    )

    st.caption(
        "Engine: Ollama • Local"
    )


    st.divider()


    if st.button(
        "Clear All Chats",
        use_container_width=True
    ):

        st.session_state.chats = []

        st.session_state.current_chat = None

        st.rerun()


# ============================================================
# MAIN
# ============================================================

chat = get_current_chat()


# ============================================================
# WELCOME
# ============================================================

if chat is None or len(
    chat["messages"]
) == 0:

    st.markdown(
        "## X"
    )

    st.markdown(
        "### How can I help you?"
    )

    st.write(
        "Ask questions, learn something new, "
        "write code, solve problems or study "
        "with X AI."
    )


    st.markdown(
        "### Quick Start"
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "Explain Python",
            use_container_width=True
        ):

            create_new_chat()

            ask_x(
                "Teach me Python programming "
                "from beginner level."
            )

            st.rerun()


    with col2:

        if st.button(
            "Help Me Study",
            use_container_width=True
        ):

            create_new_chat()

            ask_x(
                "Help me study. Ask me what "
                "subject and topic I want to learn."
            )

            st.rerun()


    col3, col4 = st.columns(2)


    with col3:

        if st.button(
            "Teach Me Something",
            use_container_width=True
        ):

            create_new_chat()

            ask_x(
                "Teach me one interesting "
                "and useful concept."
            )

            st.rerun()


    with col4:

        if st.button(
            "AutoCAD Help",
            use_container_width=True
        ):

            create_new_chat()

            ask_x(
                "Help me learn AutoCAD basics."
            )

            st.rerun()


# ============================================================
# CHAT MESSAGES
# ============================================================

if chat is not None:

    for message in chat["messages"]:

        if message["role"] == "user":

            with st.chat_message("user"):

                st.write(
                    message["content"]
                )


        else:

            with st.chat_message("assistant"):

                st.write(
                    message["content"]
                )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Message X AI..."
)


if user_input:

    ask_x(
        user_input
    )

    st.rerun()