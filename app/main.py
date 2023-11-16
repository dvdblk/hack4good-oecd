import base64
import os

import streamlit as st
from dotenv import load_dotenv

from app.preprocessing.adobe.manager import AdobeExtractAPIManager
from app.preprocessing.splitter import AdobeDocumentSplitter


@st.cache_data
def displayPDF(uploaded_file):
    """Display PDF file in Streamlit app."""
    # FIXME: Data caching should work with page numbers e.g.: #page=4
    # pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page=4" width="100%" height="320" type="application/pdf"></iframe>'

    # Read file as bytes:
    bytes_data = uploaded_file.getvalue()

    # Convert to utf-8
    base64_pdf = base64.b64encode(bytes_data).decode("utf-8")

    # Embed PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="320" type="application/pdf"></iframe>'

    # Display file
    st.markdown(pdf_display, unsafe_allow_html=True)


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
    from langchain.agents.agent_toolkits import (
        create_conversational_retrieval_agent,
        create_retriever_tool,
    )
    from langchain.chat_models import ChatOpenAI
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS

    vectorstore = FAISS.from_documents(
        AdobeDocumentSplitter().document_to_chunks(st.session_state.current_document),
        embedding=OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever()

    tool = create_retriever_tool(
        retriever,
        "search_document",
        "Searches and returns the most relevant parts of a document discussing economic policies, technologies and skills.",
    )
    tools = [tool]

    llm = ChatOpenAI(model=model, temperature=0)
    agent_executor = create_conversational_retrieval_agent(llm, tools, verbose=True)

    result = agent_executor({"input": question})
    st.write(result["output"])


def main():
    st.set_page_config(page_title="Policy Explorer 🔎", page_icon="💼")

    # Create a sidebar for docs manager
    with st.sidebar.expander("⚙️ LLModel options"):
        st.write("Choose a model to use for the analysis.")
        openai_models_tab, local_models_tab = st.tabs(["OpenAI", "Ollama (local)"])

        with openai_models_tab:
            st.write("Models provided by OpenAI hosted on their servers and require an API key.")

            # TODO: scrape openai for latest models here or use a local list with a warning
            st.session_state.oai_model = st.selectbox(
                "OpenAI Model",
                [
                    "gpt-3.5-turbo-0613",
                    "gpt-3.5-turbo-1106",
                    "gpt-4",
                    "gpt-4-1106-preview",
                ],
                help="The model choice determines the quality of the answers and price.",
            )
            st.markdown(
                "Please refer to the [OpenAI Models documentation](https://platform.openai.com/docs/models/) for more information."
            )

        with local_models_tab:
            st.write("Models provided by Ollama that can run locally but require setup.")

            local_model = st.selectbox(
                "Ollama Model",
                # TODO: implement GET localhost/api/tags https://github.com/jmorganca/ollama/blob/main/docs/api.md#list-local-models to populate the list below
                ["mistral:7b", "llama2"],
            )

    with st.sidebar.expander("📖 Documents", expanded=True):
        st.write(
            "Here you can upload any policy document(s) in PDF format. To update the list simply remove or add more docs below and click on 'Upload PDF(s)'."
        )
        # Store the uploaded PDF documents in a list
        raw_pdf_documents = st.file_uploader(
            "Upload your PDF document(s)",
            type="pdf",
            accept_multiple_files=True,
            help="Upload any document(s) in .pdf format. 🏛️",
        )
        if st.button("Process"):
            with st.spinner("Processing..."):
                # TODO: Identify if the PDF documents are new (hash the first few and last pages + page count)
                # TODO: Identify the language of the documents (load with pypdf2 and use langdetect)

                if not raw_pdf_documents:
                    st.warning("Please select a PDF document first.")
                else:
                    # Call extract API here
                    document = st.session_state.adobe_extract_api_manager.get_document(
                        raw_pdf_documents[0].getvalue(), input_file_name=raw_pdf_documents[0].name
                    )
                    st.session_state.current_document = document
                    plural = "s" if len(raw_pdf_documents) > 1 else ""
                    st.write(f"Done! Uploaded {len(raw_pdf_documents)} document{plural}.")
                    print(document.subsections, document.title)
                    displayPDF(raw_pdf_documents[0])

    st.title("OECD Policy Doc Explorer 🔎")

    analysis_tab, chat_tab = st.tabs(["📊 Analysis", "💬 Chat"])

    with analysis_tab:
        st.header("Analysis")

        with st.container():
            st.write("<Summarized document goes here>")

        with st.container():
            st.write("<Skills go here>")

    with chat_tab:
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
