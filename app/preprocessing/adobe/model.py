import io
import re
import weakref
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Optional, Set

import pandas as pd


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

    def __init__(self, raw_text: str, origin: TextOrigin, aside: bool = False) -> None:
        """
        Args:
            raw_text (str): The text of the paragraph
            origin (TextOrigin): The origin of the text in this paragraph
            aside (bool, optional): Whether the paragraph is an aside (elements that are next to a table or a figure).
                                     Defaults to `False`.
        """
        self.raw_text = raw_text
        self.origin = origin
        self.aside = aside

    def __repr__(self) -> str:
        return f"<Paragraph ({self.origin}) text={self.raw_text}>"

    @property
    def text(self) -> Optional[str]:
        if self.origin == TextOrigin.TABLE:
            # csv to markdown
            return pd.read_csv(io.StringIO(self.raw_text)).to_markdown()
        else:
            return self.raw_text


class Section:
    """
    Describe a section of the document.
    Each section is separated and detected by Adobe Extract API by headers (H1, H2, ..., Hn).

    Every section has a list of paragraphs that are contained in it along with an optional
    list of subsections.
    """

    def __init__(
        self,
        id: str,
        title: Optional[str] = None,
        pages: Optional[Set[int]] = None,
        section_type: Optional[str] = None,
        paragraphs: Optional[List[Paragraph]] = None,
        subsections: Optional[List["Section"]] = None,
        parent: Optional["Section"] = None,
    ) -> None:
        """
        Args:
            id (str): The unique ID of the section used in the LLM context (e.g. 1.1.1)
            title (Optional[str], optional): The title of the section. Defaults to `None`.
            pages (Optional[Set[int]], optional): The pages that the section spans. Defaults to `None`.
            section_type (Optional[str], optional): The type of the section. Defaults to `None`.
            paragraphs (Optional[List[Paragraph]], optional): The paragraphs of the section. Defaults to `None`.
            subsections (Optional[List[Section]], optional): The subsections of the section. Defaults to `None`.
            parent (Optional[Section], optional): The parent section of the section. Defaults to `None`.
        """
        self.id = ""
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

    @property
    def starting_page(self) -> Optional[int]:
        """Return the starting page of the section if it has any pages"""
        if pages := sorted(self.pages):
            return pages[0]
        else:
            return None

    @property
    def title_clean(self) -> Optional[str]:
        """Return a cleaned version of the title (without section number)"""
        return re.sub(r"^(\d+\.?)+", "", self.title).lstrip()

    @property
    def paragraph_text(self) -> str:
        """Return the text of all paragraphs in the section"""
        return "\n".join([p.text for p in self.paragraphs if p.text])

    @property
    def text(self) -> Optional[str]:
        """Create a simple linear text representation of the document"""
        text = ""
        for paragraph in self.paragraphs:
            text += paragraph.text + "\n"
        for subsection in self.subsections:
            text += subsection.title + "\n"
            text += subsection.text
        return text

    @property
    def all_sections(self) -> List["Section"]:
        """Return a list of all sections including all subsections"""
        sections = []
        if subsections := self.subsections:
            for subsection in subsections:
                sections.append(subsection)
                if s := subsection.all_sections:
                    sections.extend(s)
        return sections


class Document(Section):
    """The root node to a tree of Sections"""

    def __init__(
        self,
        file_path: str,
        title: Optional[str] = None,
        pages: Optional[Set[int]] = None,
        paragraphs: Optional[List[str]] = None,
        subsections: Optional[List["Section"]] = None,
        parent: Optional["Section"] = None,
    ) -> None:
        # The file_path of the document (.../UK_02.pdf)
        self.file_path = file_path
        super().__init__("root", title, pages, "document", paragraphs, subsections, parent)

    @property
    def n_pages(self) -> int:
        """Return the number of pages in the document"""
        # Recursively go to the last nested subsection and get the last page
        return sorted(self.all_sections[-1].pages)[-1]

    def get_section_by_id(self, section_id: str) -> Optional[Section]:
        """Return a section by its ID"""
        for section in self.all_sections:
            if section.id == section_id:
                return section
        return None
