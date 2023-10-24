from typing import Any, Generator, List, Tuple

import pdfplumber
from pdf2text.preprocess import PreprocessorManager
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTChar, LTFigure, LTItem, LTRect, LTTextContainer

from .model import ExtractedPage


# TODO: Move this to formatter.py
def table_converter(table):
    table_str = ""
    # Iterate over rows of the table
    for row_num in range(len(table)):
        row = table[row_num]

        # Remove the line breaker from the wrapper texts
        cleaned_row = []
        for item in row:
            if item is not None and "\n" in item:
                cleaned_row.append(item.replace("\n", " "))
            elif item is None:
                cleaned_row.append("None")
            else:
                cleaned_row.append(item)

        # Convert the table into a string
        table_str += "|" + "|".join(cleaned_row) + "|" + "\n"

    table_str = table_str[:-1]
    return table_str


class TextExtractor:
    """Analyze each page of a PDF document and extract text (works with tables and images)"""

    def __init__(self) -> None:
        self.preprocessor = PreprocessorManager()

    def _extract_text(
        self, element: LTItem, include_formatting: bool = True
    ) -> Tuple[str, List[Any]]:
        """Extract text and format from a LTItem element"""
        # Extract text from the in-line text element
        line_text = element.get_text()
        # Call preprocessors
        line_text = self.preprocessor.preprocess_text(line_text)

        if include_formatting:
            # Find formats of the text
            # init the list with all the formats that appeared in the line of text
            line_formats = []
            for text_line in element:
                if isinstance(text_line, LTTextContainer):
                    # For each character in the text line
                    for character in text_line:
                        if isinstance(character, LTChar):
                            line_formats.append(character.fontname)
                            line_formats.append(character.size)

            format_per_line = list(set(line_formats))
        else:
            format_per_line = []

        return line_text, format_per_line

    def _extract_table(self, pdf, page_num: int, table_num: int):
        # Find the examined page
        table_page = pdf.pages[page_num]
        # Extract the appropriate table
        table = table_page.extract_tables()[table_num]
        return table

    def _extract_image(self):
        """Extract text from an image"""
        # TODO: Add nougat or possibly tesseract here
        pass

    def extract(self, pdf_file) -> Generator[ExtractedPage, None, None]:
        """"""
        # Open pdf in plumber
        pdf = pdfplumber.open(pdf_file)

        # Iterate over pages
        for page_nr, page in enumerate(extract_pages(pdf_file)):
            page_text, line_format, text_from_images, text_from_tables, page_content = (
                [],
                [],
                [],
                [],
                [],
            )

            table_num = 0
            first_element = True
            table_extraction_flag = False

            page_tables = pdf.pages[page_nr]

            # Find the number of tables on the page
            tables = page_tables.find_tables()

            # Find all the elements
            page_elements = [(element.y1, element) for element in page._objs]
            # Sort all the elements as they appear in the page
            page_elements.sort(key=lambda a: a[0], reverse=True)

            # Iterate elements that compose a page
            for i, component in enumerate(page_elements):
                # Extract the element of the page layout
                element = component[1]
                # Check if element is a text element
                if isinstance(element, LTTextContainer):
                    # Check if the text appeared in a table
                    if table_extraction_flag == False:
                        # Use the function to extract the text and format for each text element
                        (line_text, format_per_line) = self._extract_text(element)
                        if line_text is not None:
                            # Append the text of each line to the page text
                            page_text.append(line_text)
                            # Append the format for each line containing text
                            line_format.append(format_per_line)
                            page_content.append(line_text)
                    else:
                        # Omit the text that appeared in a table
                        pass

                # Check if element is a figure/image
                if isinstance(element, LTFigure):
                    # TODO: Add method to convert PDF to image
                    pass
                    # TODO: Add method to extract text from image
                    pass
                    # Both could be replaced by feeding the page to Nougat directly

                # Check if element is a table
                if isinstance(element, LTRect):
                    # If the first rectangular element
                    if first_element == True and (table_num + 1) <= len(tables):
                        # Find the bounding box of the table
                        lower_side = page.bbox[3] - tables[table_num].bbox[3]
                        upper_side = element.y1
                        # Extract the information from the table
                        table = self._extract_table(pdf, page_nr, table_num)
                        # Convert the table information in structured string format
                        table_string = table_converter(table)
                        # Append the table string into a list
                        text_from_tables.append(table_string)
                        page_content.append(table_string)
                        # Set the flag as True to avoid the content again
                        table_extraction_flag = True
                        # Make it another element
                        first_element = False
                        # Add a placeholder in the text and format lists
                        page_text.append("table")
                        line_format.append("table")

                    # Check if we already extracted the tables from the page
                    if element.y0 >= lower_side and element.y1 <= upper_side:
                        pass
                    elif not isinstance(page_elements[i + 1][1], LTRect):
                        table_extraction_flag = False
                        first_element = True
                        table_num += 1

            # Yield result
            yield ExtractedPage(
                page_nr=page_nr,
                text=page_text,
                formats=line_format,
                tables_text=text_from_tables,
                images_text=text_from_images,
                content=page_content,
            )
