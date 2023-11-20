import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

from app.gui.utils import display_pdf, display_section_tree
from app.llm import OpenAIPromptExecutor
from app.preprocessing.adobe.manager import AdobeExtractAPIManager
from app.preprocessing.adobe.splitter import DocumentSplitter


def init_state():
    """Initialize the state with reusable objects."""
    # Initialize Adobe Extract API manager
    if "adobe_extract_api_manager" not in st.session_state:
        st.session_state["adobe_extract_api_manager"] = AdobeExtractAPIManager(
            client_id=os.getenv("ADOBE_CLIENT_ID"),
            client_secret=os.getenv("ADOBE_CLIENT_SECRET"),
            # FIXME: Path selectable by user?
            extract_dir_path="data/interim/000-adobe-extract",
        )


def query_llm(question, model):
    if prompt_executor := st.session_state.prompt_executor:
        result = prompt_executor.temp(question)
        print(prompt_executor.total_cost)
        print(prompt_executor.n_prompt_tokens)
        st.write(result)


def main():
    st.set_page_config(page_title="OECD Policy Explorer", page_icon="💼")

    # Sidebar - Expander: Document selection
    with st.sidebar.expander("📖 Document", expanded=True):
        st.write(
            "Upload any policy document in PDF format. To change the file simply upload a new one and click on 'Process' again."
        )
        # Store the uploaded PDF document in a list
        raw_pdf_document = st.file_uploader(
            "Browse local files to upload a document:",
            type="pdf",
            accept_multiple_files=False,
            help="📁 Allowed document file format: '.pdf'",
        )
        print(raw_pdf_document)
        if st.button("Process", type="primary"):
            with st.spinner("Processing..."):
                # TODO: Identify if the PDF document is new (hash the first few and last pages + page count)
                # TODO: Identify the language of the document (load with pypdf2 and use langdetect)

                if not raw_pdf_document:
                    st.warning("Please select a PDF document first.")
                else:
                    # Call extract API here
                    document = st.session_state.adobe_extract_api_manager.get_document(
                        raw_pdf_document.getvalue(), input_file_name=raw_pdf_document.name
                    )
                    st.session_state.current_document = document
                    st.write("Done processing selected document!")
                    st.write(f"Document has {len(document.subsections)} main sections.")
                    print(document.subsections, document.title)
                    display_pdf(raw_pdf_document)

    # Sidebar - Expander: LLM Options
    with st.sidebar.expander("⚙️ LLModel options"):
        st.write("Choose a model to use for the analysis.")

        st.write("Models provided by OpenAI are hosted on their servers and require an API key.")

        # TODO: scrape openai for latest models here or use a local list with a warning
        model = st.selectbox(
            "OpenAI Model",
            [
                "gpt-3.5-turbo-1106",
                "gpt-4",
            ],
            # index=None,
            placeholder="Choose a model",
            help="💡 The model choice determines the quality of the answers and overall price.",
        )
        # init / update oai_model
        if "oai_model" not in st.session_state:
            st.session_state.oai_model = model
        elif st.session_state.oai_model != model:
            st.session_state.oai_model = model
        # init / update prompt_executor
        if "prompt_executor" not in st.session_state:
            st.session_state["prompt_executor"] = OpenAIPromptExecutor(llm=ChatOpenAI(model=model))
        else:
            if model != st.session_state.prompt_executor.llm:
                st.session_state.prompt_executor.llm = ChatOpenAI(model=model)

        st.caption(
            "Please refer to the [OpenAI Models documentation](https://platform.openai.com/docs/models/) for more information."
        )

    # Sidebar - Expander: Cost Breakdown
    with st.sidebar.expander("💵 Cost breakdown", expanded=False):
        st.write(
            "Here you can find the total cost breakdown of the analysis and QnA. The values get reset when you change the model or fully refresh the page (F5)."
        )
        if prompt_executor := st.session_state.prompt_executor:
            st.markdown(
                f"| input tokens | output tokens | # llm requests |\n| --- | --- | --- |\n| {prompt_executor.n_prompt_tokens} | {prompt_executor.n_completion_tokens} | {prompt_executor.n_successful_requests} |"
            )
            st.subheader(
                f"Total cost: ${prompt_executor.total_cost:.6f}",
                help="💡 Press '**R**' to refresh the cost breakdown values.",
            )
        st.caption(
            "The cost is calculated based on the model choice and the number of *tokens* needed to answer all prompts. To find out more please refer to [OpenAI pricing](https://openai.com/pricing)."
        )

    st.title("OECD Policy Doc Explorer 🔎")

    analysis_tab, qna_tab = st.tabs(["📊 Analysis", "💬 QnA"])

    with analysis_tab:
        # Section tree with summaries
        st.subheader("Document overview", help="💡 Sections are provided by Adobe Extract API.")
        st.caption("Click on a section to see the summary and reveal respective subsections.")
        if "current_document" in st.session_state:
            display_section_tree(_document=st.session_state.current_document, summaries={})
            st.caption(
                "Summaries are generated only for the paragraphs in the section (not including paragraphs from subsections)."
            )
        with st.container():
            df = pd.read_csv("data/UK_34_binary_datasheet.csv")

            import json

            sheet = json.load(open("data/binary_datasheet.json"))
            existing_stis = [key for key in list(sheet.keys()) if sheet[key]["general"] == "1"]

            st.selectbox("Select STIs", existing_stis)

            st.dataframe(df)

        with st.expander("Mini-report #1: Summary of the document"):
            st.write("<Summarized document goes here>")

        with st.expander("Mini-report #2: ..."):
            st.write("")

    with qna_tab:
        st.write(
            "Here you can ask any questions about the document and get answers from the model."
        )
        st.markdown(
            "> Note that this is not a chatbot, but a question answering system without memory. Each question is treated independently."
        )

        chat_input = st.text_input("Ask a question here")

        if chat_input:
            query_llm(chat_input, st.session_state.oai_model)

        chat_question_choice_pressed = st.button("Examples")

        if chat_question_choice_pressed:
            selected_question = st.selectbox(
                "Select a question", ["What are the skills mentioned in this document?"]
            )


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    # Initialize default state (instances etc.)
    init_state()
    # Run the app
    main()
