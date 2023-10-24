from typing import Optional

from pdf2text.model import PDFElementType


class PreprocessResult:
    """Base class for a preprocessing result from a preprocessor method."""

    def __init__(self, operation, text=None):
        self.operation = operation
        self.text = text


class ModifiedPreprocessResult(PreprocessResult):
    """Result storing class for a preprocess operation that should modify the element."""

    def __init__(self, text):
        super().__init__("MODIFY", text)


class RemovedPreprocessResult(PreprocessResult):
    """Result storing class for a preprocess operation that should remove the element."""

    def __init__(self):
        super().__init__("REMOVE")


_preprocessors = {
    PDFElementType.TABLE: [],
    PDFElementType.IMAGE: [],
    PDFElementType.TEXT: [],
}


def _register_preprocessor(element_type: str):
    """Decorator to register a preprocessing step for a specific element type."""

    def decorator(func):
        _preprocessors[element_type].append(func)
        return func

    return decorator


class PreprocessorManager:
    """Class that contains preprocessing methods which are called on each paragraph of the extracted document."""

    def preprocess(self, element_type: PDFElementType, element: str) -> Optional[str]:
        """Preprocess a single text element"""
        # For each preprocessor for this element type
        for preprocessor in _preprocessors[element_type]:
            # Run the preprocessor
            result = preprocessor(element)
            # Check result
            if isinstance(result, ModifiedPreprocessResult):
                element = result.text
            elif isinstance(result, RemovedPreprocessResult):
                # If one of the preprocessors determines we should delete the element, return None
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
    return ModifiedPreprocessResult(line.replace("\n", ""))


@_register_preprocessor(PDFElementType.TEXT)
def remove_empty_lines(line: str) -> PreprocessResult:
    """Removes empty lines"""
    if line.strip() == "":
        return RemovedPreprocessResult()
