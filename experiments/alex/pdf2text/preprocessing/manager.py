from typing import Optional

from pdf2text.models import PDFContentSource, PDFContentScope
from pdf2text.preprocessing.decorator import _preprocessors

# Do not remove this import. (registers the preprocessor methods correctly)
# pylint: disable=wildcard-import,unused-wildcard-import
from pdf2text.preprocessing.methods import *


class PreprocessorManager:
    """Calls preprocessor methods on each paragraph ("line" or element) of the extracted document."""

    def _preprocess(self, preprocessor_methods, element: str) -> Optional[str]:
        """Preprocess a single text element"""
        # For each preprocessor for this element type
        for preprocessor in preprocessor_methods:
            # Run the preprocessor
            element = preprocessor(element)
            # Check result
            if element is None:
                # If one of the preprocessors determines we should delete the element, return None
                # immediately and stop the processing of this element
                return None

        return element

    def preprocess_text(self, element: str, scope: PDFContentScope) -> Optional[str]:
        """Preprocess a single text element"""
        return self._preprocess(_preprocessors[PDFContentSource.TEXT][scope], element)

    def preprocess_table(self, element: str) -> Optional[str]:
        """Preprocess a single table element"""
        return self._preprocess(_preprocessors[PDFContentSource.TABLE], element)

    def preprocess_image(self, element: str) -> Optional[str]:
        """Preprocess a single image element"""
        return self._preprocess(_preprocessors[PDFContentSource.IMAGE], element)
