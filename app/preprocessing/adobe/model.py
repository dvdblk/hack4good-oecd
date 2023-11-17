import re
import weakref
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Optional, Set


@dataclass
class AdobeExtractedPDF:
    """Model for an Adobe Extracted PDF zip file that gets produced by Adobe Extract API."""

    json_data: Dict[str, Any]
    """'structuredData.json' file from the zip file."""
    file_path: str
    """Path to the zip that contains the extracted PDF data."""
    csv_tables: Dict[str, List[str]]
    """Dictionary of CSV tables extracted from the PDF."""


@dataclass
class InterimElement:
    """Represent any element in the document that is about to be processed further."""

    raw: Dict[str, Any]
    """JSON object from the Adobe Extract API"""
    is_aside: bool
    """Whether the element is an aside (elements that are next to a table or a figure)"""
    path: str
    """The path of the element in the document without the //Document prefix and other useless parts"""

    @property
    def text(self) -> Optional[str]:
        """The text of the element"""
        # Preprocess
        if result := self.raw.get("Text"):
            # Remove 3x or more consecutive underscores or dots
            result = re.sub(r"(\_|\.){3,}", "", result)
            # Remove trailing whitespace
            result = result.rstrip()
            # Check if is numeric or is digit and return None if so
            if result.isnumeric() or result.isdigit():
                return None
            # Remove empty paragraphs
            if result == "" or result == "\n":
                return None

            return result
        else:
            return None

    @property
    def page(self) -> Optional[int]:
        """The page of the element"""
        return self.raw.get("Page")

    @property
    def full_path(self) -> Optional[str]:
        """The full path of the element in the document as provided by Adobe Extract API"""
        return self.raw.get("Path")


class TextOrigin(StrEnum):
    """Enumeration to describe the origin of a text"""

    TOC = "TOC"
    """Text came from the Table of contents"""
    PARAGRAPH = "PARAGRAPH"
    """A regular paragraph of text"""
    LIST = "LIST"
    """Text came from within a list of items"""
    TABLE = "TABLE"
    """Text came from a table (usually contains the entire table text)"""
    FIGURE = "FIGURE"
    """Text came from a figure"""


class Paragraph:
    """Describe a paragraph of text."""

    def __init__(self, text: str, origin: TextOrigin, aside: bool = False) -> None:
        """
        Args:
            text (str): The text of the paragraph
            origin (TextOrigin): The origin of the text in this paragraph
            aside (bool, optional): Whether the paragraph is an aside (elements that are next to a table or a figure).
                                     Defaults to `False`.
        """
        self.text = text
        self.origin = origin
        self.aside = aside

    def __repr__(self) -> str:
        return f"<Paragraph ({self.origin}) text={self.text}>"


class Section:
    """
    Describe a section of the document.
    Each section is separated and detected by Adobe Extract API by headers (H1, H2, ..., Hn).

    Every section has a list of paragraphs that are contained in it along with an optional
    list of subsections.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        pages: Optional[Set[int]] = None,
        section_type: Optional[str] = None,
        paragraphs: Optional[List[str]] = None,
        subsections: Optional[List["Section"]] = None,
        parent: Optional["Section"] = None,
    ) -> None:
        self.title = title
        self.pages = pages if pages else set()
        self.section_type = section_type
        self.paragraphs = paragraphs if paragraphs else []
        # Use a weakref to avoid circular references
        self.parent: Optional[weakref.ReferenceType[Section]] = (
            weakref.ref(parent) if parent else None
        )
        self.subsections: List[Section] = subsections if subsections else []

    def __repr__(self) -> str:
        return f"<Section ({self.section_type}) title={self.title}>"


class Document(Section):
    """The root node to a tree of Sections"""

    def __init__(
        self,
        title: Optional[str] = None,
        pages: Optional[Set[int]] = None,
        paragraphs: Optional[List[str]] = None,
        subsections: Optional[List["Section"]] = None,
        parent: Optional["Section"] = None,
    ) -> None:
        super().__init__(title, pages, "document", paragraphs, subsections, parent)
