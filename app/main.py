import streamlit as st

from app.config import Config
from app.gui import init_state
from app.gui.body import main_content
from app.gui.sidebar import (
    cost_breakdown_expander,
    document_selection_expander,
    llm_options_expander,
)


def main(config: Config):
    """Main entrypoint for the Streamlit app."""
    st.set_page_config(page_title="OECD Policy Explorer", page_icon="💼")

    # Sidebar - Expander: Document selection
    raw_pdf_document = document_selection_expander()
    # Sidebar - Expander: LLM Options
    llm_options_expander(config)
    # Sidebar - Expander: Cost Breakdown
    cost_breakdown_expander()

    # Body (Main content)
    st.title("OECD Policy Doc Explorer 🔎")
    main_content(config, raw_pdf_document)


if __name__ == "__main__":
    # Create config (includes env variables)
    cfg = Config(extract_dir_path="./data/interim/000-adobe-extract", data_path="./data")
    # Initialize default state (instances etc.)
    init_state(cfg)
    # Run the app
    main(cfg)
