import streamlit as st
from groq import Groq
from datetime import datetime
import ast
import operator


# ============================================================
# X AI
# ============================================================

MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """
You are X AI, a helpful personal AI assistant.

Your name is X AI.

Be friendly, clear, accurate, and useful.
Answer in a simple way when the user asks simple questions.
For school questions, explain step by step.
For programming questions, provide correct and practical code.
Do not pretend to have access to information you do not have.
If you are unsure, say so clearly.
"""


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="X AI",
    page_icon="X",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #0e1117;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .x-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .x-subtitle {
        color: #9ca3af;
        font-size: 16px;
        margin-top: 2px;
        margin-bottom: 25px;
    }

    .info-card {
        padding: 15px;
        border-radius: 12px;
        background: #171b23;
        border: 1px solid #292f3a;
        margin-bottom: 12px;
    }

    .info-title {
        font-size: 13px;
        color: #9ca3af;
        margin-bottom: 5px;
    }

    .info-value {
        font-size: 15px;
        font-weight: 600;
    }

    .welcome {
        padding: 25px;
        border-radius: 16px;
        background: #151922;
        border: 1px solid #292f3a;
        margin-bottom: 20px;
    }

    .welcome h2 {
        margin-top: 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "chats" not in st.session_state:
    st.session_state.chats = {
        "New Chat": []
    }

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_current_messages():
    return st.session_state.chats[
        st.session_state.current_chat
    ]


def create_new_chat():
    number = 1
    while f"New Chat {number}" in st.session_state.chats:
        number += 1

    name = f"New Chat {number}"
    st.session_state.chats[name] = []
    st.session_state.current_chat = name


def clear_current_chat():
    st.session_state.chats[
        st.session_state.current_chat
    ] = []


def safe_calculate(expression):
    """
    Safe calculator for basic arithmetic.
    """

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(node):

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid number")

        if isinstance(node, ast.Num):
            return node.n

        if isinstance(node, ast.BinOp):
            if type(node.op) not in allowed_operators:
                raise ValueError("Operator not allowed")

            left = evaluate(node.left)
            right = evaluate(node.right)

            return allowed_operators[type(node.op)](
                left,
                right
            )

        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in allowed_operators:
                raise ValueError("Operator not allowed")

            return allowed_operators[type(node.op)](
                evaluate(node.operand)
            )

        raise ValueError("Invalid expression")

    tree = ast.parse(expression, mode="eval")
    return evaluate(tree.body)


def local_command(message):
    """
    Handles X AI's local commands.
    Returns None when the message is not a local command.
    """

    text = message.strip()

    if text.lower() == "/time":
        return datetime.now().strftime(
            "The current local time is %I:%M:%S %p."
        )

    if text.lower() == "/date":
        return datetime.now().strftime(
            "Today's date is %A, %d %B %Y."
        )

    if text.lower() == "/help":
        return """
### X AI Commands

`/time` — Show the current time.

`/date` — Show today's date.

`/calc 25*4` — Calculate a mathematical expression.

`/help` — Show available commands.
"""

    if text.lower().startswith("/calc"):
        expression = text[5:].strip()

        if not expression:
            return "Please use the calculator like this: `/calc 25*4`"

        try:
            result = safe_calculate(expression)
            return f"Result: **{result}**"
        except Exception:
            return "I couldn't calculate that expression. Try something like `/calc 25*4`."

    return None


# ============================================================
# GROQ
# ============================================================

def get_groq_client():

    if "GROQ_API_KEY" not in st.secrets:
        return None

    api_key = st.secrets["GROQ_API_KEY"]

    if not api_key:
        return None

    return Groq(api_key=api_key)


def ask_x(user_message):

    messages = get_current_messages()

    # Local commands first
    local_reply = local_command(user_message)

    if local_reply is not None:
        messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": local_reply
            }
        )

        return local_reply

    # Add user message
    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    client = get_groq_client()

    if client is None:
        return (
            "X AI cannot find GROQ_API_KEY. "
            "Please add GROQ_API_KEY in Streamlit Cloud → Settings → Secrets."
        )

    api_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    api_messages.extend(messages)

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=api_messages,
            temperature=0.6,
            max_completion_tokens=2048,
            reasoning_effort="low",
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "I didn't receive a response from the model."

        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer

    except Exception as e:

        # Remove the user message if the API request failed
        if messages and messages[-1]["role"] == "user":
            messages.pop()

        error_text = str(e)

        return f"Groq connection error:\n\n`{error_text}`"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## X")

    st.caption("Personal Cloud AI")

    st.divider()

    st.markdown("### Chats")

    if st.button(
        "+ New Chat",
        use_container_width=True
    ):
        create_new_chat()
        st.rerun()

    chat_names = list(st.session_state.chats.keys())

    selected_chat = st.selectbox(
        "Your chats",
        chat_names,
        index=chat_names.index(
            st.session_state.current_chat
        ),
        label_visibility="collapsed",
    )

    if selected_chat != st.session_state.current_chat:
        st.session_state.current_chat = selected_chat
        st.rerun()

    st.divider()

    st.markdown("### X AI")

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">Model</div>
            <div class="info-value">{MODEL}</div>
        </div>

        <div class="info-card">
            <div class="info-title">Engine</div>
            <div class="info-value">Groq Cloud</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "Clear Conversation",
        use_container_width=True
    ):
        clear_current_chat()
        st.rerun()


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="x-title">X</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="x-subtitle">Personal Cloud AI</div>',
    unsafe_allow_html=True
)


# ============================================================
# WELCOME
# ============================================================

messages = get_current_messages()

if len(messages) == 0:

    st.markdown(
        """
        <div class="welcome">

        <h2>Welcome to X AI</h2>

        <p>
        Your personal AI assistant powered by Groq Cloud.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Quick Start")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "Explain Python",
            use_container_width=True
        ):
            st.session_state.pending_prompt = (
                "Teach me Python programming from the basics "
                "with simple examples."
            )
            st.rerun()

    with col2:
        if st.button(
            "Help me study",
            use_container_width=True
        ):
            st.session_state.pending_prompt = (
                "Help me study. Ask me what subject and topic "
                "I want to learn, then teach it step by step."
            )
            st.rerun()

    with col3:
        if st.button(
            "Teach me something",
            use_container_width=True
        ):
            st.session_state.pending_prompt = (
                "Teach me one interesting and useful concept "
                "in a simple way."
            )
            st.rerun()


# ============================================================
# DISPLAY CHAT
# ============================================================

for message in messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# PENDING QUICK-START PROMPT
# ============================================================

if "pending_prompt" in st.session_state:

    prompt = st.session_state.pending_prompt

    del st.session_state.pending_prompt

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("X is thinking..."):

        answer = ask_x(prompt)

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.rerun()


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Message X AI..."
)


if user_input:

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("X is thinking..."):

        answer = ask_x(user_input)

    with st.chat_message("assistant"):
        st.markdown(answer)
