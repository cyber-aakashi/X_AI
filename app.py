import streamlit as st
import urllib.request
import urllib.error
import json
import ast
import operator
from datetime import datetime


# ============================================================
# X AI - CONFIGURATION
# ============================================================

APP_NAME = "X AI"
MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="X AI",
    page_icon="X",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# IMPORTANT: ALL CSS IS INSIDE THIS STRING
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */
    .stApp {
        background: #080b10;
        color: #f5f7fa;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #10151c;
        border-right: 1px solid #252d38;
    }

    /* Sidebar logo */
    .x-logo {
        font-size: 58px;
        font-weight: 800;
        color: white;
        line-height: 1;
        margin-top: 5px;
        margin-bottom: 4px;
    }

    .x-subtitle {
        color: #9ba3af;
        font-size: 14px;
        margin-bottom: 28px;
    }

    /* Main welcome card */
    .welcome-card {
        background: #10151c;
        border: 1px solid #293342;
        border-radius: 18px;
        padding: 45px 35px;
        margin-bottom: 30px;
        text-align: center;
    }

    .welcome-x {
        font-size: 72px;
        font-weight: 800;
        color: white;
        margin-bottom: 10px;
    }

    .welcome-title {
        font-size: 30px;
        font-weight: 700;
        color: white;
        margin-bottom: 12px;
    }

    .welcome-text {
        font-size: 16px;
        color: #9ba3af;
        line-height: 1.7;
    }

    /* Quick Start */
    .quick-title {
        font-size: 23px;
        font-weight: 700;
        color: white;
        margin-bottom: 15px;
    }

    /* Chat bubbles */
    .user-message {
        background: #18202a;
        border: 1px solid #293342;
        border-radius: 14px;
        padding: 15px 18px;
        margin: 10px 0;
    }

    .assistant-message {
        background: #10151c;
        border: 1px solid #293342;
        border-radius: 14px;
        padding: 15px 18px;
        margin: 10px 0 20px 0;
    }

    .message-label {
        font-size: 12px;
        font-weight: 700;
        color: #9ba3af;
        margin-bottom: 7px;
        text-transform: uppercase;
    }

    /* Sidebar chat names */
    .chat-label {
        color: #dce1e8;
        font-size: 14px;
        padding: 5px 0;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid #303a48;
        background: #151c25;
        color: #f5f7fa;
        min-height: 42px;
    }

    .stButton > button:hover {
        border-color: #657185;
        color: white;
    }

    /* Hide Streamlit decoration */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }

    </style>
    """,
    unsafe_allow_html=True
)


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
    chat_number = len(st.session_state.chats) + 1

    chat = {
        "name": f"New Chat {chat_number}",
        "messages": []
    }

    st.session_state.chats.append(chat)
    st.session_state.current_chat = len(st.session_state.chats) - 1


def get_current_chat():
    if st.session_state.current_chat is None:
        return None

    if st.session_state.current_chat >= len(st.session_state.chats):
        return None

    return st.session_state.chats[st.session_state.current_chat]


def delete_chat(index):
    if 0 <= index < len(st.session_state.chats):

        st.session_state.chats.pop(index)

        if len(st.session_state.chats) == 0:
            st.session_state.current_chat = None

        elif st.session_state.current_chat >= len(st.session_state.chats):
            st.session_state.current_chat = len(st.session_state.chats) - 1


def rename_chat_if_needed(chat, first_message):
    if len(chat["messages"]) == 1:
        name = first_message.strip()

        if len(name) > 28:
            name = name[:28] + "..."

        chat["name"] = name


# ============================================================
# CALCULATOR
# ============================================================

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    expression = expression.strip()

    tree = ast.parse(expression, mode="eval")

    def calculate(node):

        if isinstance(node, ast.Expression):
            return calculate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value

        if isinstance(node, ast.BinOp):
            left = calculate(node.left)
            right = calculate(node.right)

            operation = ALLOWED_OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Operator not allowed")

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):
            value = calculate(node.operand)

            operation = ALLOWED_OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Operator not allowed")

            return operation(value)

        raise ValueError("Invalid calculation")

    return calculate(tree)


# ============================================================
# LOCAL COMMANDS
# ============================================================

def handle_local_command(message):

    text = message.strip()
    lower = text.lower()

    # Time
    if lower in ["/time", "time", "what is the time", "current time"]:
        return "The current local time is " + datetime.now().strftime("%I:%M:%S %p")

    # Date
    if lower in ["/date", "date", "today", "what is today's date"]:
        return "Today's date is " + datetime.now().strftime("%d %B %Y")

    # Calculator
    if lower.startswith("/calc "):

        expression = text[6:].strip()

        try:
            answer = safe_calculate(expression)
            return f"Answer: {answer}"
        except Exception:
            return "I couldn't calculate that. Try something like: /calc 25*4+10"

    # Help
    if lower in ["/help", "help"]:

        return """
### X AI Commands

**Time**
`/time`

**Date**
`/date`

**Calculator**
`/calc 25*4+10`

You can also simply ask me normal questions.
"""

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

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(request, timeout=120) as response:

            result = json.loads(response.read().decode("utf-8"))

            if "message" in result and "content" in result["message"]:
                return result["message"]["content"]

            return "X AI received an unexpected response from Ollama."

    except urllib.error.URLError:

        return (
            "I can't connect to Ollama right now.\n\n"
            "Please make sure Ollama is running and that the "
            f"`{MODEL}` model is installed."
        )

    except Exception as error:

        return f"X AI connection error: {error}"


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are X AI, a helpful personal AI assistant.

Your goals:

1. Give clear and useful answers.
2. Help with programming.
3. Help students study.
4. Explain difficult topics simply.
5. Help with Python, C, HTML, CSS and JavaScript.
6. Help with AutoCAD and technical subjects.
7. Show calculations clearly.
8. Be friendly and concise.
9. If the user asks for code, provide complete working code.
10. Do not pretend to have internet access when you do not.
"""


# ============================================================
# ASK X
# ============================================================

def ask_x(user_message):

    chat = get_current_chat()

    if chat is None:

        create_new_chat()

        chat = get_current_chat()

    # Save user message
    chat["messages"].append(
        {
            "role": "user",
            "content": user_message
        }
    )

    rename_chat_if_needed(chat, user_message)

    # Check local commands first
    local_answer = handle_local_command(user_message)

    if local_answer is not None:

        chat["messages"].append(
            {
                "role": "assistant",
                "content": local_answer
            }
        )

        return local_answer

    # Prepare messages for Ollama
    ollama_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for message in chat["messages"]:

        ollama_messages.append(
            {
                "role": message["role"],
                "content": message["content"]
            }
        )

    answer = ask_ollama(ollama_messages)

    chat["messages"].append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    return answer


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="x-logo">X</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="x-subtitle">Personal Local AI</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "+ New Chat",
        use_container_width=True
    ):

        create_new_chat()
        st.rerun()

    st.markdown("---")

    st.markdown("### Chats")

    if len(st.session_state.chats) == 0:

        st.caption("No chats yet.")

    else:

        for index, chat in enumerate(st.session_state.chats):

            col1, col2 = st.columns([5, 1])

            with col1:

                if st.button(
                    chat["name"],
                    key=f"open_chat_{index}",
                    use_container_width=True
                ):

                    st.session_state.current_chat = index
                    st.rerun()

            with col2:

                if st.button(
                    "×",
                    key=f"delete_chat_{index}"
                ):

                    delete_chat(index)
                    st.rerun()

    st.markdown("---")

    st.markdown("### X AI")

    st.caption(f"Model: {MODEL}")
    st.caption("Engine: Ollama • Local")

    st.markdown("---")

    if st.button(
        "Clear All Chats",
        use_container_width=True
    ):

        st.session_state.chats = []
        st.session_state.current_chat = None
        st.rerun()


# ============================================================
# MAIN AREA
# ============================================================

chat = get_current_chat()


# ============================================================
# WELCOME SCREEN
# ============================================================

if chat is None or len(chat["messages"]) == 0:

    st.markdown(
        """
        <div class="welcome-card">

            <div class="welcome-x">X</div>

            <div class="welcome-title">
                How can I help you?
            </div>

            <div class="welcome-text">
                Ask questions, learn something new,
                write code, solve problems or study with X AI.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="quick-title">Quick Start</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Explain Python",
            use_container_width=True
        ):

            create_new_chat()

            st.session_state.current_chat = (
                len(st.session_state.chats) - 1
            )

            ask_x(
                "Teach me Python programming from beginner level."
            )

            st.rerun()

    with col2:

        if st.button(
            "Help Me Study",
            use_container_width=True
        ):

            create_new_chat()

            st.session_state.current_chat = (
                len(st.session_state.chats) - 1
            )

            ask_x(
                "Help me study. Ask me what subject and topic I want to learn."
            )

            st.rerun()

    col3, col4 = st.columns(2)

    with col3:

        if st.button(
            "Teach Me Something",
            use_container_width=True
        ):

            create_new_chat()

            st.session_state.current_chat = (
                len(st.session_state.chats) - 1
            )

            ask_x(
                "Teach me one interesting and useful concept."
            )

            st.rerun()

    with col4:

        if st.button(
            "AutoCAD Help",
            use_container_width=True
        ):

            create_new_chat()

            st.session_state.current_chat = (
                len(st.session_state.chats) - 1
            )

            ask_x(
                "Help me learn AutoCAD basics."
            )

            st.rerun()


# ============================================================
# CHAT DISPLAY
# ============================================================

if chat is not None:

    for message in chat["messages"]:

        if message["role"] == "user":

            st.markdown(
                '<div class="user-message">'
                '<div class="message-label">You</div>'
                + message["content"]
                + "</div>",
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                '<div class="assistant-message">'
                '<div class="message-label">X AI</div>'
                + message["content"].replace("\n", "<br>")
                + "</div>",
                unsafe_allow_html=True
            )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Message X AI..."
)


if user_input:

    ask_x(user_input)

    st.rerun()