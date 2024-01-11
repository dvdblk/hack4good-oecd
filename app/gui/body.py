import json

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.config import Config
from app.gui.css import css_qna
from app.gui.utils import (
    create_mini_report,
    display_section_tree,
    get_summaries,
    qna_flow,
)


def main_content(config: Config, raw_pdf_document: UploadedFile):
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

                    sheet = json.load(open(config.data_path / "binary_datasheet.json"))
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
                    css_qna,
                    unsafe_allow_html=True,
                )
                for question, result in st.session_state.qna_pairs:
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
