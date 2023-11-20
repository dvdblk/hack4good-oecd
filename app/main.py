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
        st.write(result)


@st.cache_data
def get_summaries(_document, file_path):
    """
    Args:
        _document: AdobeExtractAPIManager.get_document() object
        file_path: path to the file (not used within the method, only used as the st.cache_data caching key)
    """
    if prompt_executor := st.session_state.prompt_executor:
        if document := st.session_state.current_document:
            summaries = prompt_executor.create_summaries_chain(document.all_sections)
            st.session_state.summaries_dict = summaries
        else:
            st.warning("Please select a document first.")
    else:
        st.warning("Please select a document first.")


def main():
    st.set_page_config(page_title="OECD Policy Explorer", page_icon="💼")

    # Sidebar - Expander: Document selection
    with st.sidebar.expander("📖 Document", expanded=True):
        st.write(
            "Upload any policy document in PDF format. To change the file simply upload a new one and click on 'Extract' again."
        )
        # Store the uploaded PDF document in a list
        raw_pdf_document = st.file_uploader(
            "Browse local files to upload a document:",
            type="pdf",
            accept_multiple_files=False,
            help="📁 Allowed document file format: '.pdf'",
        )

        if st.button(
            "Extract",
            type="primary",
            help="🤖 Extracts text and structural information from the selected document.",
        ):
            with st.spinner(
                "Processing... (this might take around 2-3 minutes if the document is new)"
            ):
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
                    st.session_state.uploaded_file = raw_pdf_document
                    if "summaries_dict" in st.session_state:
                        del st.session_state.summaries_dict

        if "uploaded_file" in st.session_state and "current_document" in st.session_state:
            doc = st.session_state.current_document
            st.write(
                f"Document has {doc.n_pages} pages of extracted text and {len(doc.subsections)} main sections."
            )
            display_pdf(st.session_state.uploaded_file)

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
            st.session_state["prompt_executor"] = OpenAIPromptExecutor(
                llm=ChatOpenAI(model=model, temperature=0, timeout=10)
            )
        else:
            if model != st.session_state.prompt_executor.llm:
                st.session_state.prompt_executor.llm = ChatOpenAI(
                    model=model, temperature=0, timeout=10
                )

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

    placeholder = st.empty()

    if "summaries_dict" not in st.session_state:
        with placeholder.container():
            if "current_document" not in st.session_state:
                st.write("Please upload (and extract) a document in the sidebar first.")
            else:
                st.write(
                    "Document loaded! If you want to start the analysis or QnA, generating a summary is required."
                )
                st.caption(
                    "Note: This operation already costs money and it might take a while so please be patient :)"
                )
                if st.button("Analyze", type="primary"):
                    with st.spinner("Analyzing document..."):
                        get_summaries(st.session_state.current_document, raw_pdf_document)

                        st.write("☑️ Success!")
    else:
        with placeholder.container():
            analysis_tab, qna_tab = st.tabs(["📊 Analysis", "💬 QnA"])

            with analysis_tab:
                # Section tree with summaries
                st.subheader(
                    "Document overview",
                    help="💡 Sections are provided by Adobe Extract API.",
                )
                st.write("Click on a section to see the summary and reveal respective subsections.")
                if "current_document" in st.session_state:
                    display_section_tree(
                        _document=st.session_state.current_document,
                        summaries=st.session_state.summaries_dict or {},
                    )
                    st.caption(
                        "Summaries are generated only for the paragraphs in the section (not including paragraphs from subsections)."
                    )
                    st.caption(
                        '⚠️ It is in your best interest to verify the summaries contain some meaningful text before proceeding to the QnA tab. A small number of documents are not OCR\'d correctly and thus might be relatively empty, resulting in a lot of "table of contents" or "references" summaries.'
                    )
                with st.container():
                    df = pd.read_csv("data/UK_34_binary_datasheet.csv")

                    import json

                    sheet = json.load(open("data/binary_datasheet.json"))
                    existing_stis = [
                        key for key in list(sheet.keys()) if sheet[key]["general"] == "1"
                    ]

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
                    "> Note that this is not a chatbot, but a question answering system without conversation memory. Each question is treated independently of the previous ones."
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
