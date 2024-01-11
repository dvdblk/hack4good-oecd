import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.config import Config
from app.gui import init_prompt_executor
from app.gui.utils import display_pdf


def document_selection_expander() -> UploadedFile:
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

        return raw_pdf_document


def llm_options_expander(config: Config):
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
            help="💡 The model choice determines the quality of the answers and overall cost.",
        )
        # init / update oai_model
        if "oai_model" not in st.session_state:
            st.session_state.oai_model = model
        elif st.session_state.oai_model != model:
            st.session_state.oai_model = model
        # init / update prompt_executor
        init_prompt_executor(model, config)

        st.caption(
            "Please refer to the [OpenAI Models documentation](https://platform.openai.com/docs/models/) for more information."
        )


def cost_breakdown_expander():
    with st.sidebar.expander("💵 Cost breakdown", expanded=False):
        st.write("Here you can find the total cost breakdown of the analysis and QnA.")
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
        st.caption("⚠️ The cost gets reset to 0 if you refresh the page (F5) or change the model.")
