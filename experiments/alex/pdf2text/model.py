"""Model of a processed page in a PDF document."""
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
    """Describe the different types of elements in a PDF document that we work with."""

    TABLE = "table"
    IMAGE = "image"
    TEXT = "text"
