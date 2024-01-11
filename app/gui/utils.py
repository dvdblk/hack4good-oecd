"""Utility functions for displaying various elements"""
__all__ = [
    "display_pdf",
    "display_section_tree",
]

import base64

import streamlit as st

from app.gui.css import css_mini_report, section_tree_css
from app.preprocessing.adobe.model import Document


@st.cache_data
def display_pdf(uploaded_file):
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


def display_section_tree(_document: Document, summaries: dict):
    """Display section tree in Streamlit app."""
    result_markdown = section_tree_css

    def add_hierarchy_tree(section, level=0):
        result_markdown = '<div id="tree">'
        # should_add_expander = summaries.get(section.id) or section.subsections
        # always add expander
        should_add_expander = True
        if should_add_expander:
            # Add details tag
            result_markdown += "<details><summary>"

        # Add section title and page number
        result_markdown += f'<span id="treeTitle">{section.title}</span><span id="pageNr">{section.starting_page+1}</span>'

        if should_add_expander:
            # Close details tag
            result_markdown += "</summary>"

        summary = summaries.get(section.id)
        result_markdown += f"<blockquote>Section summary: {summary or 'This section has no standalone text in its paragraphs.'}</blockquote>"

        if section.subsections:
            result_markdown += "<ul>"
            for subsection in section.subsections:
                result_markdown += "<li>"
                result_markdown += add_hierarchy_tree(subsection, level + 1)
                result_markdown += "</li>"
            result_markdown += "</ul>"

        if should_add_expander:
            result_markdown += "</details>"
        return result_markdown + "</div>"

    if _document.subsections:
        for section in _document.subsections:
            result_markdown += f"\n* "
            # Iterate over main sections (needs newline)
            result_markdown += add_hierarchy_tree(section)
    else:
        result_markdown = "No sections found in the document 😕"

    st.markdown(
        result_markdown,
        unsafe_allow_html=True,
    )


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
    Creates a new mini report (visual element) for the given question.

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
                css_mini_report,
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
