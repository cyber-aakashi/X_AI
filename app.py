import streamlit as st
import urllib.request
import urllib.error
import json
import ast
import operator
from datetime import datetime


# ============================================================
# X AI SETTINGS
# ============================================================

APP_NAME = "X AI"
MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="X AI - Personal AI Assistant",
    page_icon="X",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "chats" not in st.session_state:
    st.session_state.chats = []

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "theme" not in st.session_state:
    st.session_state.theme = "dark"


# ============================================================
# THEME
# ============================================================

if st.session_state.theme == "dark":
    BG = "#080b10"
    SIDEBAR_BG = "#10151c"
    CARD_BG = "#10151c"
    USER_BG = "#18202a"
    BORDER = "#293342"
    TEXT = "#f5f7fa"
    MUTED = "#9ba3af"
    BUTTON_BG = "#151c25"
    BUTTON_BORDER = "#303a48"
else:
    BG = "#f5f7fa"
    SIDEBAR_BG = "#ffffff"
    CARD_BG = "#ffffff"
    USER_BG = "#eef2f7"
    BORDER = "#d9dee7"
    TEXT = "#111827"
    MUTED = "#5b6472"
    BUTTON_BG = "#ffffff"
    BUTTON_BORDER = "#cbd2dc"


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background: {BG};
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}

    section[data-testid="stSidebar"] {{
        background: {SIDEBAR_BG};
        border-right: 1px solid {BORDER};
    }}

    .x-logo {{
        font-size: 58px;
        font-weight: 800;
        color: {TEXT};
        text-align: center;
        line-height: 1;
        margin: 5px 0 4px 0;
    }}

    .x-subtitle {{
        color: {MUTED};
        font-size: 14px;
        text-align: center;
        margin-bottom: 28px;
    }}

    .welcome-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 45px 35px;
        margin-bottom: 30px;
        text-align: center;
    }}

    .welcome-x {{
        font-size: 72px;
        font-weight: 800;
        color: {TEXT};
        margin-bottom: 10px;
    }}

    .welcome-title {{
        font-size: 30px;
        font-weight: 700;
        color: {TEXT};
        margin-bottom: 12px;
    }}

    .welcome-text {{
        font-size: 16px;
        color: {MUTED};
        line-height: 1.7;
    }}

    .quick-title {{
        font-size: 23px;
        font-weight: 700;
        color: {TEXT};
        margin-bottom: 15px;
    }}

    .user-message {{
        background: {USER_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 15px 18px;
        margin: 10px 0;
        color: {TEXT};
        word-wrap: break-word;
    }}

    .assistant-message {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 15px 18px;
        margin: 10px 0 20px 0;
        color: {TEXT};
        word-wrap: break-word;
    }}

    .message-label {{
        font-size: 12px;
        font-weight: 700;
        color: {MUTED};
        margin-bottom: 7px;
        text-transform: uppercase;
    }}

    .stButton > button {{
        border-radius: 10px;
        border: 1px solid {BUTTON_BORDER};
        background: {BUTTON_BG};
        color: {TEXT};
        min-height: 42px;
    }}

    .stButton > button:hover {{
        border-color: {MUTED};
        color: {TEXT};
    }}

    div[data-baseweb="select"] > div {{
        background: {BUTTON_BG};
        border-color: {BUTTON_BORDER};
        color: {TEXT};
    }}

    [data-testid="stChatInput"] {{
        background: {CARD_BG};
    }}

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    header {{
        background: transparent;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


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
                "I couldn't calculate that.\n\n"
                "Try: /calc 25*4+10"
            )

    if lower in ["/help", "help"]:

        return (
            "X AI Commands\n\n"
            "/time - current time\n\n"
            "/date - today's date\n\n"
            "/calc 25*4+10 - calculator\n\n"
            "/help - show commands\n\n"
            "You can also ask normal questions."
        )

    return None


# ============================================================
# AI SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are X AI, a helpful personal AI assistant.

Give clear, useful and accurate answers.

You can help with:
- Programming
- Python
- C
- HTML
- CSS
- JavaScript
- Mathematics
- Engineering subjects
- AutoCAD
- Studying
- General questions

Explain difficult topics simply.

When the user asks for code, provide complete working code.

Be friendly and concise.

Do not claim to have abilities you do not have.
"""


# ============================================================
# GROQ API KEY
# ============================================================

def get_groq_key():

    try:

        key = st.secrets.get("GROQ_API_KEY")

        if key is None:
            return None

        key = str(key).strip()

        if not key:
            return None

        return key

    except Exception:

        return None


# ============================================================
# GROQ REQUEST
# ============================================================

def ask_groq(messages):

    api_key = get_groq_key()

    if api_key is None:

        return (
            "X AI is not connected to Groq.\n\n"
            "Open your Streamlit Cloud app settings "
            "and add this secret:\n\n"
            "GROQ_API_KEY\n\n"
            "Do not put the API key directly inside app.py."
        )

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.6,
        "max_completion_tokens": 2048,
        "top_p": 0.95,
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        GROQ_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
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

        if not choices:
            return "X AI received an empty response from Groq."

        message = choices[0].get("message", {})

        content = message.get("content")

        if content:
            return str(content)

        return "X AI received a response without text."

    except urllib.error.HTTPError as error:

        try:
            details = error.read().decode("utf-8")
        except Exception:
            details = ""

        if error.code == 400:

            return (
                "Groq returned HTTP 400.\n\n"
                "The request was rejected.\n\n"
                "Model: " + MODEL + "\n\n"
                "Details:\n" + details
            )

        if error.code == 401:

            return (
                "Groq returned HTTP 401.\n\n"
                "Your GROQ_API_KEY is invalid or expired.\n\n"
                "Check the key in Streamlit Cloud Secrets."
            )

        if error.code == 403:

            return (
                "Groq returned HTTP 403.\n\n"
                "The request was forbidden.\n\n"
                "Model: " + MODEL + "\n\n"
                "Details:\n" + details
            )

        if error.code == 429:

            return (
                "Groq returned HTTP 429.\n\n"
                "The rate limit was reached. "
                "Please try again later."
            )

        return (
            "Groq returned HTTP "
            + str(error.code)
            + ".\n\n"
            + details
        )

    except urllib.error.URLError as error:

        return (
            "X AI could not connect to Groq Cloud.\n\n"
            + str(error)
        )

    except Exception as error:

        return (
            "X AI connection error.\n\n"
            + str(error)
        )


# ============================================================
# MAIN AI FUNCTION
# ============================================================

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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "<div class='x-logo'>X</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='x-subtitle'>Personal Cloud AI</div>",
        unsafe_allow_html=True
    )

    theme_choice = st.radio(
        "Appearance",
        ["Dark", "Light"],
        index=(
            0
            if st.session_state.theme == "dark"
            else 1
        )
    )

    new_theme = theme_choice.lower()

    if new_theme != st.session_state.theme:

        st.session_state.theme = new_theme
        st.rerun()

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

            col1, col2 = st.columns(
                [5, 1]
            )

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

    st.caption(
        "Theme: "
        + st.session_state.theme.title()
    )

    st.markdown("---")

    if st.button(
        "Clear All Chats",
        use_container_width=True
    ):

        st.session_state.chats = []
        st.session_state.current_chat = None
        st.rerun()


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    "<div class='x-logo'>X</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='x-subtitle'>Personal AI Assistant</div>",
    unsafe_allow_html=True
)


# ============================================================
# CURRENT CHAT
# ============================================================

chat = get_current_chat()


# ============================================================
# WELCOME SCREEN
# ============================================================

if chat is None or len(chat["messages"]) == 0:

    st.markdown(
        """
        <div class='welcome-card'>
            <div class='welcome-x'>X</div>
            <div class='welcome-title'>
                How can I help you?
            </div>
            <div class='welcome-text'>
                Ask questions, learn something new,
                write code, solve problems or study with X AI.
            </div>
        </div>
        """,
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


# ============================================================
# DISPLAY CHAT
# ============================================================

if chat is not None:

    for message in chat["messages"]:

        content = message["content"]

        safe_content = (
            str(content)
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


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Message X AI..."
)

if user_input:

    ask_x(user_input)
    st.rerun()
