"""Preprocessing methods (steps) for pdf elements are defined in this file."""
import re

from typing import Optional
from pdf2text.preprocessing.decorator import register_preprocessor
from pdf2text.models import PDFContentSource, PDFContentScope


@register_preprocessor(source=PDFContentSource.TEXT, scope=PDFContentScope.LINE)
def remove_newlines(line: str) -> Optional[str]:
    """Removes all newline occurences in the text."""
    return line.replace("\n", "")


@register_preprocessor(PDFContentSource.TEXT, PDFContentScope.LINE)
def remove_unnecessary_whitespace(line: str) -> Optional[str]:
    """Removes unnecessary whitespace"""
    return re.sub(r"\s+", " ", line)


@register_preprocessor(PDFContentSource.TEXT, PDFContentScope.LINE)
def remove_empty_lines(line: str) -> Optional[str]:
    """Removes empty lines"""
    whitespace_removed = re.sub(r"\s", "", line)
    if whitespace_removed == "":
        # Return None to indicate that this line should be removed
        return None
    else:
        # Identity
        return line


# @register_preprocessor(PDFContentSource.TEXT, PDFContentScope.PARAGRAPH)
def remove_numbers(paragraph: str) -> Optional[str]:
    """Removes numbers including decimal points or surrounded by brackets"""
    return re.sub(r"\(?\d+\.?\d*\)?", "", paragraph)


@register_preprocessor(PDFContentSource.TEXT, PDFContentScope.PARAGRAPH)
def remove_index_dots(line: str) -> Optional[str]:
    """Removes index dots inside the line"""
    return re.sub(r"\s*(\.\ |\.){4,}\s*", "", line)


@register_preprocessor(PDFContentSource.TEXT, PDFContentScope.PARAGRAPH)
def remove_numeric_lines(paragraph: str) -> Optional[str]:
    if paragraph.isnumeric():
        return None
    else:
        return paragraph


@register_preprocessor(PDFContentSource.TEXT, PDFContentScope.PARAGRAPH)
def remove_empty_paragraphs(paragraph: str) -> Optional[str]:
    """Removes empty paragraphs"""
    if paragraph.strip() == "":
        # Return None to indicate that this paragraph should be removed
        return None
    else:
        # Identity
        return paragraph


@register_preprocessor(PDFContentSource.TEXT, PDFContentScope.PAGE)
def remove_empty_pages(page: str) -> Optional[str]:
    """Removes empty pages"""
    if page.strip() == "":
        # Return None to indicate that this page should be removed
        return None
    else:
        # Identity
        return page
