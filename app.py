import streamlit as st
import urllib.request
import urllib.error
import json
import ast
import operator
from datetime import datetime

APP_NAME = "X AI"
MODEL = "llama-3.1-8b-instant"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(
    page_title="X AI",
    page_icon="X",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .stApp {
        background: #080b10;
        color: #f5f7fa;
    }

    section[data-testid="stSidebar"] {
        background: #10151c;
        border-right: 1px solid #252d38;
    }

    .x-logo {
        font-size: 58px;
        font-weight: 800;
        color: white;
        text-align: center;
        line-height: 1;
        margin: 5px 0 4px 0;
    }

    .x-subtitle {
        color: #9ba3af;
        font-size: 14px;
        text-align: center;
        margin-bottom: 28px;
    }

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

    .quick-title {
        font-size: 23px;
        font-weight: 700;
        color: white;
        margin-bottom: 15px;
    }

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

if "chats" not in st.session_state:
    st.session_state.chats = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


def create_new_chat():
    number = len(st.session_state.chats) + 1

    chat = {
        "name": "New Chat " + str(number),
        "messages": []
    }

    st.session_state.chats.append(chat)
    st.session_state.current_chat = len(st.session_state.chats) - 1


def get_current_chat():
    index = st.session_state.current_chat

    if index is None:
        return None

    if index < 0 or index >= len(st.session_state.chats):
        return None

    return st.session_state.chats[index]


def delete_chat(index):
    if index < 0 or index >= len(st.session_state.chats):
        return

    st.session_state.chats.pop(index)

    if len(st.session_state.chats) == 0:
        st.session_state.current_chat = None

    elif st.session_state.current_chat >= len(st.session_state.chats):
        st.session_state.current_chat = len(st.session_state.chats) - 1


def rename_chat_if_needed(chat, message):
    if len(chat["messages"]) != 1:
        return

    name = message.strip()

    if len(name) > 28:
        name = name[:28] + "..."

    chat["name"] = name


ALLOWED_OPERATORS = {
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
    tree = ast.parse(expression.strip(), mode="eval")

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


def handle_local_command(message):
    text = message.strip()
    lower = text.lower()

    if lower in [
        "/time",
        "time",
        "what is the time",
        "current time"
    ]:
        return (
            "The current local time is "
            + datetime.now().strftime("%I:%M:%S %p")
        )

    if lower in [
        "/date",
        "date",
        "today",
        "what is today's date"
    ]:
        return (
            "Today's date is "
            + datetime.now().strftime("%d %B %Y")
        )

    if lower.startswith("/calc "):
        expression = text[6:].strip()

        try:
            result = safe_calculate(expression)
            return "Answer: " + str(result)

        except Exception:
            return (
                "I couldn't calculate that. "
                "Try /calc 25*4+10"
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


SYSTEM_PROMPT = (
    "You are X AI, a helpful personal AI assistant. "
    "Give clear and useful answers. "
    "Help with programming and studying. "
    "Explain difficult topics simply. "
    "Help with Python, C, HTML, CSS and JavaScript. "
    "Help with AutoCAD and technical subjects. "
    "Show calculations clearly. "
    "Be friendly and concise. "
    "When asked for code, provide complete working code. "
    "Do not claim to have abilities you do not have."
)


def ask_groq(messages):
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return (
            "X AI is not connected to Groq yet.\n\n"
            "Please add GROQ_API_KEY in Streamlit Cloud Secrets."
        )

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048,
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        GROQ_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        choices = result.get("choices", [])

        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")

            if content:
                return content

        return "X AI received an unexpected response from Groq."

    except urllib.error.HTTPError as error:
        try:
            details = error.read().decode("utf-8")
        except Exception:
            details = ""

        if error.code == 401:
            return (
                "X AI could not authenticate with Groq.\n\n"
                "Check GROQ_API_KEY in Streamlit Cloud Secrets."
            )

        if error.code == 429:
            return (
                "X AI reached the current Groq rate limit. "
                "Please try again later."
            )

        return (
            "Groq error "
            + str(error.code)
            + ":\n\n"
            + details
        )

    except urllib.error.URLError:
        return (
            "X AI could not connect to the cloud AI service. "
            "Please try again."
        )

    except Exception as error:
        return (
            "X AI connection error:\n\n"
            + str(error)
        )


def ask_x(user_message):
    chat = get_current_chat()

    if chat is None:
        create_new_chat()
        chat = get_current_chat()

    chat["messages"].append(
        {
            "role": "user",
            "content": user_message
        }
    )

    rename_chat_if_needed(
        chat,
        user_message
    )

    local_answer = handle_local_command(
        user_message
    )

    if local_answer is not None:
        chat["messages"].append(
            {
                "role": "assistant",
                "content": local_answer
            }
        )

        return local_answer

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

    answer = ask_groq(messages)

    chat["messages"].append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    return answer


with st.sidebar:
    st.markdown(
        "<div class='x-logo'>X</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='x-subtitle'>Personal Cloud AI</div>",
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

    if not st.session_state.chats:
        st.caption("No chats yet.")

    else:
        for index, chat_item in enumerate(
            st.session_state.chats
        ):
            col1, col2 = st.columns([5, 1])

            with col1:
                if st.button(
                    chat_item["name"],
                    key="open_chat_" + str(index),
                    use_container_width=True
                ):
                    st.session_state.current_chat = index
                    st.rerun()

            with col2:
                if st.button(
                    "X",
                    key="delete_chat_" + str(index)
                ):
                    delete_chat(index)
                    st.rerun()

    st.markdown("---")
    st.markdown("### X AI")

    st.caption(
        "Model: " + MODEL
    )

    st.caption(
        "Engine: Groq Cloud"
    )

    st.markdown("---")

    if st.button(
        "Clear All Chats",
        use_container_width=True
    ):
        st.session_state.chats = []
        st.session_state.current_chat = None
        st.rerun()


chat = get_current_chat()

if chat is None or len(chat["messages"]) == 0:
    st.markdown(
        "<div class='welcome-card'>"
        "<div class='welcome-x'>X</div>"
        "<div class='welcome-title'>How can I help you?</div>"
        "<div class='welcome-text'>"
        "Ask questions, learn something new, write code, "
        "solve problems or study with X AI."
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='quick-title'>Quick Start</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Explain Python",
            use_container_width=True
        ):
            create_new_chat()

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

            ask_x(
                "Help me learn AutoCAD basics."
            )

            st.rerun()


if chat is not None:
    for message in chat["messages"]:
        content = message["content"]

        safe_content = (
            content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

        if message["role"] == "user":
            st.markdown(
                "<div class='user-message'>"
                "<div class='message-label'>You</div>"
                + safe_content
                + "</div>",
                unsafe_allow_html=True
            )

        else:
            st.markdown(
                "<div class='assistant-message'>"
                "<div class='message-label'>X AI</div>"
                + safe_content
                + "</div>",
                unsafe_allow_html=True
            )


user_input = st.chat_input("Message X AI...")

if user_input:
    ask_x(user_input)
    st.rerun()