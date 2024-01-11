import streamlit as st
from langchain.chat_models import ChatOpenAI

from app.config import Config
from app.llm import OpenAIPromptExecutor
from app.preprocessing.adobe.manager import AdobeExtractAPIManager


def init_state(config: Config):
    """Initialize the session state with reusable objects."""
    # Initialize Adobe Extract API manager
    if "adobe_extract_api_manager" not in st.session_state:
        st.session_state["adobe_extract_api_manager"] = AdobeExtractAPIManager(
            client_id=config.adobe_client_id,
            client_secret=config.adobe_client_secret,
            extract_dir_path=config.extract_dir_path,
        )

    # Default user input
    if "qna_input" not in st.session_state:
        st.session_state["qna_input"] = ""

    if "qna_pairs" not in st.session_state:
        st.session_state["qna_pairs"] = []


def init_prompt_executor(model: str, config: Config):
    if "prompt_executor" not in st.session_state:
        st.session_state["prompt_executor"] = OpenAIPromptExecutor(
            llm=ChatOpenAI(
                model=model,
                temperature=config.openai_model_temperature,
                timeout=config.openai_timeout,
                api_key=config.openai_api_key,
            )
        )
    else:
        if model != st.session_state.prompt_executor.llm:
            st.session_state.prompt_executor.llm = ChatOpenAI(
                model=model,
                temperature=config.openai_model_temperature,
                timeout=config.openai_timeout,
                api_key=config.openai_api_key,
            )
