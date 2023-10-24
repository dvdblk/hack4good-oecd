from pdf2text.model import PDFElementType

__preprocessors = {
    PDFElementType.TABLE: [],
    PDFElementType.IMAGE: [],
    PDFElementType.TEXT: [],
}


def _register_preprocessor(element_type: str):
    """Decorator to register a preprocessing step for a specific element type."""

    def decorator(func):
        __preprocessors[element_type].append(func)
        return func

    return decorator
