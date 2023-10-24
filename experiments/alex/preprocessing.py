"""Multistep preprocessing pipeline for pdf2text

Mostly based on: https://towardsdatascience.com/extracting-text-from-pdf-files-with-python-a-comprehensive-guide-9fc4003d517

reqs:   PyPDF2, pdfminer.six, pdfplumber
"""

import argparse
import os

import pdfplumber
import PyPDF2
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTChar, LTFigure, LTRect, LTTextContainer
from PIL import Image


def analyze_pdf(pdf_path):
    """Analyze PDF file and return text"""

    # Iterate over pages
    for pagenum, page in enumerate(extract_pages(pdf_path)):
        # Iterate elements that compose a page
        for element in page:
            # Check if element is a text element
            if isinstance(element, LTTextContainer):
                # Method to extract text from text block
                pass
                # Method to extract text format

            if isinstance(element, LTFigure):
                # TODO: Add method to convert PDF to image
                pass
                # TODO: Add method to extract text from image
                pass
                # Both could be replaced by feeding the page to Nougat directly

            if isinstance(element, LTRect):
                # Method to extract table
                pass
                # Method to convert table content to string
                pass


def main():
    parser = argparse.ArgumentParser(description="Convert OECD PDF to text")
    parser.add_argument("-p", "--pdf", type=str, help="Path to PDF file", required=True)
    args = parser.parse_args()

    # Extract text from PDF
    print(f"Extracting text from '{args.pdf}' ...")


if __name__ == "__main__":
    main()
