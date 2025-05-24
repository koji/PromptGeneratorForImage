# app.py
import streamlit as st
from cerebras.cloud.sdk import Cerebras
import openai
import os
from dotenv import load_dotenv
from together import Together

# --- Assuming config.py and utils.py exist ---
import config
import utils


try:
    from prompt import BASE_PROMPT
except ImportError:
    st.error(
        "Error: 'prompt.py' not found or 'BASE_PROMPT' is not defined within it.")
    st.stop()

# --- Import column rendering functions ---
from chat_column import render_chat_column
from image_column import render_image_column

load_dotenv()

st.set_page_config(page_icon="🤖", layout="wide",
                   page_title="Prompt & Image Generator")


utils.display_icon("🤖")
st.title("Prompt & Image Generator")
st.subheader("Generate text prompts (left) and edit/generate images (right)",
             divider="orange", anchor=False)


api_key_from_env = os.getenv("CEREBRAS_API_KEY")
show_api_key_input = not bool(api_key_from_env)
cerebras_api_key = None
together_api_key = os.getenv("TOGETHER_API_KEY")

# --- サイドバーの設定 ---
with st.sidebar:
    st.title("Settings")
    if show_api_key_input:
        st.markdown("### :red[Enter your Cerebras API Key below]")
        api_key_input = st.text_input(
            "Cerebras API Key:", type="password", key="cerebras_api_key_input_field")
        if api_key_input:
            cerebras_api_key = api_key_input
    else:
        cerebras_api_key = api_key_from_env
        st.success("✓ Cerebras API Key loaded from environment")
    # Together Key Status
    if not together_api_key:
        st.warning(
            "TOGETHER_API_KEY environment variable not set. Image generation (right column) will not work.", icon="⚠️")
    else:
        st.success("✓ Together API Key loaded from environment")
    # Model selection
    model_option = st.selectbox(
        "Choose a LLM model:",
        options=list(config.MODELS.keys()),
        format_func=lambda x: config.MODELS[x]["name"],
        key="model_select"
    )
    # Max tokens slider
    max_tokens_range = config.MODELS[model_option]["tokens"]
    default_tokens = min(2048, max_tokens_range)
    max_tokens = st.slider(
        "Max Tokens (LLM):",
        min_value=512,
        max_value=max_tokens_range,
        value=default_tokens,
        step=512,
        help="Max tokens for the LLM's text prompt response."
    )

# Check if Cerebras API key is available
if not cerebras_api_key and show_api_key_input and 'cerebras_api_key_input_field' in st.session_state and st.session_state.cerebras_api_key_input_field:
    cerebras_api_key = st.session_state.cerebras_api_key_input_field

if not cerebras_api_key:
    st.error("Cerebras API Key is required. Please enter it in the sidebar or set the CEREBRAS_API_KEY environment variable.", icon="🚨")
    st.stop()

llm_client = None
image_client = None
try:
    llm_client = Cerebras(api_key=cerebras_api_key)

    if together_api_key:
        image_client = Together(api_key=together_api_key)
except Exception as e:
    st.error(f"Failed to initialize API client(s): {str(e)}", icon="🚨")
    st.stop()

# --- Session State Initialization ---
# Initialize state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_image_prompt_text" not in st.session_state:
    st.session_state.current_image_prompt_text = ""
# --- MODIFICATION START ---
# Replace single image state with a list to store multiple images and their prompts
if "generated_images_list" not in st.session_state:
    st.session_state.generated_images_list = []  # Initialize as empty list
# Remove old state variable if it exists (optional cleanup)
if "latest_generated_image" in st.session_state:
    del st.session_state["latest_generated_image"]
# --- MODIFICATION END ---
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None

# --- Clear history if model changes ---
if st.session_state.selected_model != model_option:
    st.session_state.messages = []
    st.session_state.current_image_prompt_text = ""
    # --- MODIFICATION START ---
    # Clear the list of generated images when model changes
    st.session_state.generated_images_list = []
    # --- MODIFICATION END ---
    st.session_state.selected_model = model_option
    st.rerun()

# --- Define Main Columns ---
chat_col, image_col = st.columns([2, 1])

# --- Render Columns using imported functions ---
with chat_col:
    render_chat_column(st, llm_client, model_option, max_tokens, BASE_PROMPT)

with image_col:
    render_image_column(st, image_client)  # Pass the client
