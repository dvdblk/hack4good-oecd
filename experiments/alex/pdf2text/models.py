"""Data models module"""
from dataclasses import dataclass
from enum import StrEnum
from typing import List


@dataclass
class ExtractedPage:
    """Model of a page extracted from a PDF document."""

    page_nr: int
    """Page number in the PDF document."""
    content: List[str]
    """All text from the page."""


class PDFContentSource(StrEnum):
    """Enum that describes the different sources of elements in a PDF document that we convert into text."""

    TABLE = "table"
    """Represents a table element in a PDF document."""
    IMAGE = "image"
    """Represents an image element. E.g. an embedded pdf page or actual image (possibly with text)"""
    TEXT = "text"
    """Represents a text element."""


class PDFContentScope(StrEnum):
    """Enum that describes the different scopes of elements in a PDF document that we convert into text."""

    LINE = "line"
    """Represents a single line of text that ends with a newline character.

    Note:   This is the smallest unit of text in a PDF document and always comes
            from a text PDFContentSource.
    """
    PARAGRAPH = "paragraph"
    """Represents a paragraph of text (multiple lines).

    Note:   This is a group of lines that were originally separated by a newline character.
            Always comes from a text PDFContentSource.
    """
    PAGE = "page"
    """Represents a page of text (multiple paragraphs).

    Note: This is a group of paragraphs that already contain text generated from images and tables.
    """
