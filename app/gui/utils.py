"""Utility functions for displaying various elements"""
__all__ = [
    "display_pdf",
    "display_section_tree",
]

import base64

import streamlit as st

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


_section_tree_css = """
<style>
#tree {
    border: 1px solid #aaa;
    border-radius: 4px;
    padding: 0.5em 0.5em 0;
}

#treeTitle {
    font-weight: bold;
    margin: -0.5em -0.5em 0;
    padding: 0.5em;
}

#tree[open] {
    padding: 0.5em;
}

#pageNr {
    font-size: 0.8em;
    float: right;
    text-color: #959698;
}

#tree ul {
  list-style-type: none;
}
</style>
"""


def display_section_tree(_document: Document, summaries: dict):
    """Display section tree in Streamlit app."""
    result_markdown = _section_tree_css

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
