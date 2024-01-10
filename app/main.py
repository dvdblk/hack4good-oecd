import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

from app.gui.utils import display_pdf, display_section_tree
from app.llm import OpenAIPromptExecutor
from app.preprocessing.adobe.manager import AdobeExtractAPIManager
from app.preprocessing.adobe.splitter import DocumentSplitter

# TODO: Move this to a config file
OPEN_AI_TIMEOUT = 30
MODEL_TEMPERATURE = 0.0


def init_state():
    """Initialize the state with reusable objects."""
    # Initialize Adobe Extract API manager
    if "adobe_extract_api_manager" not in st.session_state:
        st.session_state["adobe_extract_api_manager"] = AdobeExtractAPIManager(
            client_id=os.getenv("ADOBE_CLIENT_ID"),
            client_secret=os.getenv("ADOBE_CLIENT_SECRET"),
            # FIXME: Path selectable by user?
            extract_dir_path="/app/app/data/interim/000-adobe-extract",
        )

    if "qna_input" not in st.session_state:
        st.session_state["qna_input"] = ""

    if "qna_pairs" not in st.session_state:
        st.session_state["qna_pairs"] = []


def query_llm(question, model):
    if prompt_executor := st.session_state.prompt_executor:
        result = prompt_executor.temp(question)
        st.write(result)


def qna_flow():
    """Called on qna input 'Enter' press"""
    st.session_state.qna_input = st.session_state.qna_input_element
    st.session_state.qna_input_element = ""

    question = st.session_state.qna_input

    if prompt_executor := st.session_state.prompt_executor:
        result = prompt_executor.generic_question_chain(
            st.session_state.current_document, st.session_state.summaries_dict, question
        )

        st.session_state.qna_pairs.append((question, result))


@st.cache_data
def create_mini_report(question, document_fp):
    """
    Args:
        question: question to answer
        document_fp: path to the document (not used within the method, only used as the st.cache_data caching key)
    """
    with st.expander(f"📋 {question}"):
        if prompt_executor := st.session_state.prompt_executor:
            result = prompt_executor.generic_question_chain(
                st.session_state.current_document, st.session_state.summaries_dict, question
            )
            st.write(result.intermediate_answer)
            st.markdown(
                """
                <style>
                    .badge-container {
                        display: flex;
                        gap: 10px;
                    }

                    .badge {
                        padding: 8px 12px;
                        border-radius: 20px;
                        background-color: #25262e;
                        color: #ffffff;
                        text-align: center;
                        font-size: 12px;
                    }
                <style>
                """,
                unsafe_allow_html=True,
            )
            result_markdown = "<div class='badge-container'>"
            for s_id in result.section_ids:
                if section := st.session_state.current_document.get_section_by_id(s_id):
                    clamped_section_title = (
                        section.title[:22].lstrip() + "..."
                        if len(section.title) > 22
                        else section.title
                    )
                    result_markdown += f"<span class='badge'>{clamped_section_title}</span>"
            result_markdown += "</div>"
            st.markdown(result_markdown, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_summaries(_document, file_path):
    """
    Args:
        _document: AdobeExtractAPIManager.get_document() object
        file_path: path to the file (not used within the method, only used as the st.cache_data caching key)
    """
    if prompt_executor := st.session_state.prompt_executor:
        if document := st.session_state.current_document:
            # Summaries
            summaries_gen = prompt_executor.create_summaries_chain(document.all_sections)
            summary_progress_text = "Summarizing sections..."
            summary_progress_bar = st.progress(0, text=summary_progress_text)
            summary_dict = None
            for value in summaries_gen:
                summary_progress_bar.progress(value[0], text=summary_progress_text)
                summary_dict = value[1]
            st.session_state.summaries_dict = summary_dict
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
            help="💡 The model choice determines the quality of the answers and overall cost.",
        )
        # init / update oai_model
        if "oai_model" not in st.session_state:
            st.session_state.oai_model = model
        elif st.session_state.oai_model != model:
            st.session_state.oai_model = model
        # init / update prompt_executor
        if "prompt_executor" not in st.session_state:
            st.session_state["prompt_executor"] = OpenAIPromptExecutor(
                llm=ChatOpenAI(model=model, temperature=MODEL_TEMPERATURE, timeout=OPEN_AI_TIMEOUT)
            )
        else:
            if model != st.session_state.prompt_executor.llm:
                st.session_state.prompt_executor.llm = ChatOpenAI(
                    model=model, temperature=MODEL_TEMPERATURE, timeout=OPEN_AI_TIMEOUT
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
                st.write("Document loaded! Press 'Analyze' to proceed further.")
                st.caption(
                    "Note: This operation already costs money and it might take a while so please be patient :)"
                )
                if st.button("Analyze", type="primary"):
                    with st.spinner("Analyzing document..."):
                        get_summaries(st.session_state.current_document, raw_pdf_document)

                        st.write("☑️ Success! Please press '**R**' to refresh the page.")
    else:
        with placeholder.container():
            analysis_tab, qna_tab = st.tabs(["📊 Analysis", "💬 Document QnA"])

            with analysis_tab:
                # Section tree with summaries
                st.subheader(
                    "Document overview",
                    help="💡 Sections are provided by Adobe Extract API.",
                )

                # Mini report summary
                create_mini_report(
                    "What is the document about?",
                    document_fp=st.session_state.current_document.file_path,
                )

                st.markdown(
                    "Click on a section to reveal a summary and respective subsections.",
                    help="Summaries are generated only for the paragraphs in the section (not including paragraphs from subsections).",
                )
                if "current_document" in st.session_state:
                    display_section_tree(
                        _document=st.session_state.current_document,
                        summaries=st.session_state.summaries_dict or {},
                    )
                    st.caption(
                        '⚠️ It is in your best interest to verify the summaries contain some meaningful text before proceeding to the QnA tab. A small number of documents are not OCR\'d correctly and thus might be relatively empty, resulting in a lot of "table of contents" or "references" summaries.'
                    )

                with st.container():
                    st.subheader("Technologies and skills")
                    st.write(
                        "Here you can select from a list of technologies and then subsequent skills mentioned in the document."
                    )
                    st.caption(
                        "After choosing a topic (Technology) + subtopic (Skill) or inputting your own a set of mini reports (pre-defined questions) will be answered by the LLM."
                    )
                    df = pd.read_csv("data/UK_34_binary_datasheet.csv")
                    # st.dataframe(df)

                    import json

                    sheet = json.load(open("data/binary_datasheet.json"))
                    existing_topics = [key for key in list(sheet.keys())]

                    selected_topic = st.selectbox("Select a Topic", existing_topics)

                    topic_relevant_subtopics = sheet[selected_topic].keys()
                    selected_subtopic = st.selectbox(
                        "Select a Subtopic",
                        topic_relevant_subtopics,
                        index=None,
                        placeholder=f"No subtopic selected (using '{selected_topic}' as a general topic)",
                    )

                    if st.button("Generate mini reports", type="primary"):
                        with st.spinner("Generating mini reports..."):
                            create_mini_report(
                                f"Which skills are mentioned in relation to {selected_topic}?",
                                document_fp=st.session_state.current_document.file_path,
                            )
                            create_mini_report(
                                f"Does the document discuss specific degress, qualifications, or professions with regard to {selected_topic}, if so, how?",
                                document_fp=st.session_state.current_document.file_path,
                            )
                            create_mini_report(
                                f"What are all the policy intiatives mentioned in the document with regard to {selected_topic}?",
                                document_fp=st.session_state.current_document.file_path,
                            )

                            create_mini_report(
                                f"Is the document optimistic or pessimistic about how the skill needs for technology '{selected_topic}' are met?",
                                document_fp=st.session_state.current_document.file_path,
                            )

                            create_mini_report(
                                f"What is the most important passage about skills or technologies in the document?",
                                document_fp=st.session_state.current_document.file_path,
                            )

                            if selected_subtopic:
                                create_mini_report(
                                    f"Does the document specify how {selected_subtopic} should be promoted?",
                                    document_fp=st.session_state.current_document.file_path,
                                )
                                create_mini_report(
                                    f"Does the document discuss the funding of the programme to support the development of {selected_subtopic}?",
                                    document_fp=st.session_state.current_document.file_path,
                                )

            with qna_tab:
                st.write(
                    "In this Tab you can ask *any* questions about the document and receive answers from the model."
                )
                st.markdown(
                    "> Note that this is not a chatbot, but a question answering system without conversation memory. Each QnA is treated independently of the previous ones."
                )

                with st.expander("🤔 How to formulate a good prompt?"):
                    st.write(
                        "Prompting the model with a good question is crucial but sometimes unintuitive. Here are some prompting tips:"
                    )
                    st.markdown(
                        """

"""
                    )

                with st.expander("🏭 Example questions/prompts that tend to work well:"):
                    st.markdown(
                        """

"""
                    )

                st.divider()
                st.text_input(
                    "Ask a question (prompt) here:", key="qna_input_element", on_change=qna_flow
                )
                st.markdown(
                    """
                    <style>
                        .container {
                            padding: 20px;
                            border: 1px solid #ddd;
                            border-radius: 10px;
                            margin: 10px;
                        }
                        .question-answer {
                            display: flex;
                            flex-direction: column;
                            align-items: flex-start;
                        }
                        .emoji {
                            margin-right: 10px;
                            margin-bottom: 10px;
                        }
                        .badge-container {
                            display: flex;
                            gap: 10px;
                        }

                        .badge {
                            padding: 8px 12px;
                            border-radius: 20px;
                            background-color: #25262e;
                            color: #ffffff;
                            text-align: center;
                            font-size: 12px;
                        }
                    <style>
                    """,
                    unsafe_allow_html=True,
                )
                for question, result in st.session_state.qna_pairs:
                    # st.write(f"Q: {question}")
                    # st.write(f"A: {result}")
                    result_markdown = f"""
                        <div class='container'>
                            <div class='question-answer'>
                                <span class='emoji'>❓<strong> Question: </strong>{question}</span>
                                <span class='emoji'>🤖<strong> Answer: </strong> {result.intermediate_answer}</span>
                    """
                    for s_id in result.section_ids:
                        if section := st.session_state.current_document.get_section_by_id(s_id):
                            clamped_section_title = (
                                section.title[:22].lstrip() + "..."
                                if len(section.title) > 22
                                else section.title
                            )
                            result_markdown += f"<div class='badge-container'><span class='badge'>{clamped_section_title}</span>"

                    result_markdown += "</div></div>"
                    st.markdown(result_markdown, unsafe_allow_html=True)

                if st.session_state.qna_pairs:
                    if st.button("🗑️ Clear All"):
                        st.session_state.qna_pairs = []


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    # Initialize default state (instances etc.)
    init_state()
    # Run the app
    main()
