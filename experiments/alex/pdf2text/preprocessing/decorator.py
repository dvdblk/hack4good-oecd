from pdf2text.models import PDFElementType

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
