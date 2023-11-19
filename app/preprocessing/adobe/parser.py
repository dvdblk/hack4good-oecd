import re
from typing import List, Optional, Set, Tuple, Union

from app.logging import init_logger
from app.preprocessing.adobe.model import (
    AdobeExtractedPDF,
    Document,
    InterimElement,
    Paragraph,
    Section,
    TextOrigin,
)

logger = init_logger(__name__)


class AdobeStructuredJSONParser:
    """Parse the 'structuredJSON.json' file from an Adobe Extracted PDF zip file."""

    # TODO: refactor this abomination below :)
    def adobe_extracted_pdf_to_document(self, extracted_pdf: AdobeExtractedPDF) -> Document:
        """Convert 'structuredData.json' from Adobe Extract API .zip file to a Document instance"""
        # header_to_section_type = {
        #     "H1": "section",
        #     "H2": "subsection",
        #     "H3": "subsubsection",
        # }
        document = Document()

        curr_section = document
        section_to_insert_header = {}
        elements_iterator = iter(extracted_pdf.json_data["elements"])
        elements_stack: List[Tuple[dict, str]] = []

        def get_next_elem() -> InterimElement:
            """Uses an iterator (and a stack) to get the next element from the structured_json"""
            if elements_stack:
                return elements_stack.pop()
            else:
                element = next(elements_iterator)
                path = element.get("Path")
                if path is None:
                    raise ValueError("Path is None")

                # Verify that xpath starts with //Document
                if not path.startswith("//Document"):
                    raise ValueError(f"Path does not start with //Document: {path}")

                # Remove //Document
                path = path.replace("//Document", "", 1)

                # Check if it is an Aside element
                is_aside = False
                new_path, n_occurences = re.subn(r"^\/Aside(\[\d+\])?", "", path)
                if n_occurences == 1:
                    # remove Aside prefix
                    path = new_path
                    is_aside = True

                # Remove /Reference occurences
                new_path, n_occurences = re.subn(
                    r"\/Reference(\[\d+\])?(\/Sub(\[\d+\])?)?", "", path
                )
                if n_occurences > 0:
                    path = new_path

                # Remove /ParagraphSpan occurences
                new_path, n_occurences = re.subn(r"\/ParagraphSpan(\[\d+\])?", "", path)
                if n_occurences > 0:
                    path = new_path

                # Remove /StyleSpan occurences
                new_path, n_occurences = re.subn(r"\/StyleSpan(\[\d+\])?", "", path)
                if n_occurences > 0:
                    path = new_path

            return InterimElement(element, is_aside, path)

        def add_paragraph(paragraph: Paragraph, pages: Optional[Union[Set[int], int]]):
            if paragraph.raw_text is not None:
                curr_section.paragraphs.append(paragraph)
                if pages:
                    if isinstance(pages, int):
                        curr_section.pages.add(pages)
                    elif isinstance(pages, set):
                        curr_section.pages.update(pages)

        try:
            while True:
                element = get_next_elem()

                if re.match(r".*\/(ExtraCharSpan|DirectEntrySpan)(\[\d+\])?$", element.path):
                    # Skip extra characters
                    continue
                elif re.match(r"^\/Title$", element.path):
                    # Title
                    document.title = element.text
                elif re.match(r"^(\/P(\[\d+\])?)?\/Figure(\[\d+\])?$", element.path):
                    # Figure
                    add_paragraph(Paragraph(element.text, TextOrigin.FIGURE), pages=element.page)
                elif re.match(r"^\/P(\[\d+\])?(\/(Sub|ParagraphSpan)(\[\d+\])?)?$", element.path):
                    # Paragraph
                    add_paragraph(Paragraph(element.text, TextOrigin.PARAGRAPH), pages=element.page)
                elif re.match(r"^\/Table(\[\d+\])?.*$", element.path):
                    # Table
                    if csv_paths := element.raw.get("filePaths"):
                        # Table with data
                        # load the csvs and add them as paragraphs
                        for csv_path in csv_paths:
                            csv_text = extracted_pdf.csv_tables[csv_path]
                            add_paragraph(Paragraph(csv_text, TextOrigin.TABLE), pages=element.page)

                elif match := re.match(r"^\/(H\d)(\[\d+\])?(\/Sub(\[\d+\])?)?$", element.path):
                    # Header
                    title = element.text
                    section_type = match.group(1)

                    # Verify that this header is not the same as the previous one
                    # Check if page difference is less than 2
                    # Check if title is the same
                    if curr_section.title == title and element.page - max(curr_section.pages) < 2:
                        # Skip this header
                        continue

                    # Verify next element is a paragraph and not a followup header
                    while True:
                        next_element = get_next_elem()
                        reinsert_back = True
                        if next_match := re.match(
                            r"^\/(H\d)(\[\d+\])?(\/Sub(\[\d+\])?)?$", next_element.path
                        ):
                            if next_match.group(1) == section_type:
                                next_title = next_element.text or ""
                                if not title.endswith(" ") and not next_title.startswith(" "):
                                    title += " "
                                title += next_title
                                reinsert_back = False

                        if reinsert_back:
                            # Next element is not a header, push it to the stack
                            elements_stack.append(next_element)
                            break

                    # Create new section
                    new_section = Section(
                        id="",
                        title=title,
                        section_type=section_type,
                    )

                    # Check if new section is a subsection
                    if curr_section.section_type == "document":
                        # New section is a top level (H1) section
                        # Add it to the document
                        curr_section.subsections.append(new_section)
                        # Set parent of new section to document
                        new_section.parent = curr_section
                        # Every new H1 has to be inserted into document subsections
                        section_to_insert_header[section_type] = curr_section
                    else:
                        if section_type < curr_section.section_type:
                            # H2 -> H1 or H3 -> H2 or H3 -> H1
                            if parent_section := section_to_insert_header.get(section_type):
                                parent_section.subsections.append(new_section)
                                new_section.parent = parent_section
                            else:
                                # TODO: find closest parent of curr_section with section_type < new_section.section_type
                                raise ValueError("Could not find parent section")

                        elif section_type > curr_section.section_type:
                            # H1 -> H2 or H2 -> H3 or H1 -> H3
                            # curr_section is the parent
                            curr_section.subsections.append(new_section)
                            new_section.parent = curr_section
                            section_to_insert_header[section_type] = curr_section
                        else:
                            # H1 = H1 or H2 = H2 or H3 = H3
                            # curr_section.parent is the parent as they are on the same level
                            curr_section.parent.subsections.append(new_section)
                            new_section.parent = curr_section.parent

                    curr_section = new_section

                    # Set correct section ID
                    if new_section.parent.section_type == "document":
                        # Get index of new_section in document subsections
                        new_section.id = str(len(document.subsections))
                    else:
                        # Get index of new_section in parent subsections
                        new_section.id = (
                            new_section.parent.id + "." + str(len(new_section.parent.subsections))
                        )

                elif match := re.match(
                    r"^\/L(\[\d+\])?\/LI(\[\d+\])?\/(Lbl|LBody).*$", element.path
                ):
                    # List
                    list_item_type = match.group(3)
                    if list_item_type == "Lbl":
                        # Check if we can join it with a LBody element that should follow this one
                        next_element = get_next_elem()
                        if next_element.path == element.path.replace("Lbl", "LBody"):
                            # Join the two elements
                            joined_text = element.text or ""
                            if next_element.text:
                                if not next_element.text.startswith(" "):
                                    joined_text += " "
                                joined_text += next_element.text
                            add_paragraph(
                                Paragraph(joined_text, TextOrigin.LIST),
                                pages=set([element.page, next_element.page]),
                            )
                        else:
                            # Push next element to stack
                            elements_stack.append(next_element)
                            # Add current element as a paragraph
                            add_paragraph(
                                Paragraph(element.text, TextOrigin.LIST), pages=element.page
                            )
                    elif list_item_type == "LBody":
                        add_paragraph(Paragraph(element.text, TextOrigin.LIST), pages=element.page)
                elif match := re.match(
                    r"^\/TOC(\[\d+\])?\/TOCI(\[\d+\])?\/(Span|Lbl|LBody)(\[\d+\])?$", element.path
                ):
                    # Table of contents
                    toc_elem_type = match.group(3)
                    if toc_elem_type == "Span":
                        if text := element.text:
                            # Check if the next element is another span that should be joined
                            next_element = get_next_elem()
                            if next_element.path == element.path + "[2]":
                                # Join the two elements
                                joined_text = text
                                if next_element.text:
                                    if not next_element.text.startswith(" "):
                                        joined_text += " "
                                    joined_text += next_element.text
                                add_paragraph(
                                    Paragraph(joined_text, TextOrigin.TOC),
                                    pages=set([element.page, next_element.page]),
                                )
                            else:
                                # Push next element to stack
                                elements_stack.append(next_element)
                                # Add current element as a paragraph
                                add_paragraph(Paragraph(text, TextOrigin.TOC), pages=element.page)
                    elif toc_elem_type == "Lbl":
                        # Check if we can join it with a LBody element that should follow this one
                        next_element = get_next_elem()
                        if next_element.path == element.path.replace("Lbl", "LBody"):
                            # Join the two elements
                            joined_text = element.text or ""
                            if next_element.text:
                                if not next_element.text.startswith(" "):
                                    joined_text += " "
                                joined_text += next_element.text
                            add_paragraph(
                                Paragraph(joined_text, TextOrigin.TOC),
                                pages=set([element.page, next_element.page]),
                            )
                        else:
                            # Push next element to stack
                            elements_stack.append(next_element)
                            # Add current element as a paragraph
                            add_paragraph(
                                Paragraph(element.text, TextOrigin.TOC), pages=element.page
                            )

                elif re.match(r"^\/Footnote(\[\d+\])?$", element.path):
                    # Footnote
                    # Ignore for now
                    continue
                else:
                    add_paragraph(Paragraph(element.text, TextOrigin.PARAGRAPH), pages=element.page)
                    logger.warning(
                        f"Unknown element path: {element.path} in {extracted_pdf.file_path}"
                    )
                    # raise ValueError(f"Unknown element path: {element.path}")
        except StopIteration:
            pass

        return document
