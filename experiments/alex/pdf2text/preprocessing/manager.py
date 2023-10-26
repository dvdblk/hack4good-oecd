from typing import Optional

from pdf2text.models import PDFElementType
from pdf2text.preprocessing.decorator import _preprocessors, _register_preprocessor
from pdf2text.preprocessing.result import (
    ModifiedPreprocessResult,
    PreprocessResult,
    RemovedPreprocessResult,
)


class PreprocessorManager:
    """Calls preprocessor methods on each paragraph ("line" or element) of the extracted document."""

    def preprocess(self, element_type: PDFElementType, element: str) -> Optional[str]:
        """Preprocess a single text element / parapragh"""
        # For each preprocessor for this element type
        for preprocessor in _preprocessors[element_type]:
            # Run the preprocessor
            result = preprocessor(element)
            # Check result
            if isinstance(result, ModifiedPreprocessResult):
                element = result.text
            elif isinstance(result, RemovedPreprocessResult):
                # If one of the preprocessors determines we should delete the element, return None
                # immediately and stop the processing of this element
                return None

        return element

    def preprocess_text(self, element: str) -> Optional[str]:
        """Preprocess a single text element"""
        return self.preprocess(PDFElementType.TEXT, element)

    def preprocess_table(self, element: str) -> Optional[str]:
        """Preprocess a single table element"""
        return self.preprocess(PDFElementType.TABLE, element)

    def preprocess_image(self, element: str) -> Optional[str]:
        """Preprocess a single image element"""
        return self.preprocess(PDFElementType.IMAGE, element)


@_register_preprocessor(PDFElementType.TEXT)
def remove_newlines(line: str) -> PreprocessResult:
    """Removes all newline occurences in the text."""
    return ModifiedPreprocessResult(text=line.replace("\n", ""))


@_register_preprocessor(PDFElementType.TEXT)
def remove_empty_lines(line: str) -> PreprocessResult:
    """Removes empty lines"""
    if line.strip() == "":
        return RemovedPreprocessResult()
