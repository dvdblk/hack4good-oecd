import argparse
import os
from typing import List, Optional

from pdf2text.extract import TextExtractor
from pdfminer.psparser import PSEOF


# FIXME: Use a logger instead of prints
class PDFConverter:
    """Main class orchestrating the pdf to text conversion (for a single pdf file).

    Note:
        The full conversion pipeline is as follows:
        1. `extract` text and formats from PDF (including text from tables and images)
            a. `preprocess` the text = works on individual text paragraphs, tables, images
                                        (remove linebreaks, join words, remove whitespace etc.)
            b. `postprocess` the text = works on full pages of preprocessed text
                                        (e.g. remove first few pages of intro, blank pages,
                                        page numbers, etc.)
        2. (optional) `translate`
        3. `format` the text to the desired output
    """

    def __init__(self) -> None:
        """
        Configuration options can be passed here e.g. which translation to use
        and how to format the output.
        """
        pass

    def convert(self, file_path: str, out_path: Optional[str]) -> List[str]:
        """
        Convert a single pdf file to text.

        Args:
            file_path: Path to the pdf file or directory.
            out_path: Path to the output file.

        Returns:
            List of strings (one string per page).
        """
        pdf_file = open(file_path, "rb")

        try:
            # Run the pdf2text conversion pipeline
            pages = []
            result_text = ""
            for page in TextExtractor().extract(pdf_file):
                # Add the page to the result
                result_text += f"[Page #{page.page_nr}]\n{page.content}\n"
                pages.append(page)

            # Save to file if needed
            if out_path:
                # Create the filename but with .txt instead of .pdf
                out_filename = os.path.splitext(os.path.basename(file_path))[0] + ".txt"
                # Open the file
                out_file = open(os.path.join(out_path, out_filename), "w", encoding="utf-8")

                # Save to file
                out_file.write(result_text)
                out_file.close()

            pdf_file.close()
            return pages
        except PSEOF:
            # Unexpected end of file - probably corrupted
            print(f"File corrupted: '{file_path}'")
            return []


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Convert OECD PDF to text")
    parser.add_argument("-f", "--file", type=str, help="Path to PDF file(s)", required=True)
    parser.add_argument(
        "-p",
        "--page",
        type=int,
        help="Page number to print (works only with a single pdf file)",
        required=False,
        default=None,
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        help="Path to output file",
        required=False,
        default=None,
    )
    args = parser.parse_args()

    # Create the converter
    converter = PDFConverter()
    # Check if --file is directory
    if os.path.isdir(args.file):
        # Extract text from all PDFs in the directory
        print(f"Extracting text from all PDFs in '{args.file}' ...")
        results = []
        from tqdm import tqdm

        progress_bar = tqdm(total=len(os.listdir(args.file)))

        for file in os.listdir(args.file):
            if file.endswith(".pdf"):
                # Skip existing text files
                text_file = os.path.join(args.output_dir, file.replace(".pdf", ".txt"))
                if os.path.exists(text_file):
                    progress_bar.write(f"Skipping '{text_file}' as it already exists.")
                    progress_bar.update(1)
                    continue

                # Extract text from PDF
                file_path = os.path.join(args.file, file)
                progress_bar.write(f"Extracting text from '{file_path}' ...")
                results.append(converter.convert(file_path, args.output_dir))
                progress_bar.update(1)
        result = results[0]
    else:
        # Extract text from PDF
        print(f"Extracting text from file '{args.file}' ...")
        result = converter.convert(args.file, args.output_dir)

    # Print the result page if needed
    if args.page is not None:
        print(result[args.page])
