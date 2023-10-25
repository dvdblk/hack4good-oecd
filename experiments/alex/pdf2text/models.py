"""Data models module"""
from dataclasses import dataclass
from enum import StrEnum
from typing import List


@dataclass
class ExtractedPage:
    """Model of a page extracted from a PDF document."""

    page_nr: int
    """Page number in the PDF document."""
    text: List[str]
    """Text from the page."""
    formats: List[str]
    """All format of the text from the page. Same indexing as `text`."""
    tables_text: List[str]
    """Text from the tables in the page."""
    images_text: List[str]
    """Text from the images in the page."""
    content: List[str]
    """All text from the page."""


class PDFElementType(StrEnum):
    """Enum that describes the different types of elements in a PDF document that we work with."""

    TABLE = "table"
    """Represents a table element in a PDF document."""
    IMAGE = "image"
    """Represents an image element. E.g. an embedded pdf page or actual image (possibly with text)"""
    TEXT = "text"
    """Represents a text element."""
