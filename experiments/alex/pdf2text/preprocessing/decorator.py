from typing import Optional
from pdf2text.models import PDFContentSource, PDFContentScope
from pdf2text.preprocessing.exceptions import PreprocessingError

# Dictionary of registered preprocessors (methods that alter text)
_preprocessors = {
    PDFContentSource.TEXT: {
        PDFContentScope.LINE: [],
        PDFContentScope.PARAGRAPH: [],
        PDFContentScope.PAGE: [],
    },
    PDFContentSource.TABLE: [],
    PDFContentSource.IMAGE: [],
}


def register_preprocessor(source: PDFContentSource, scope: Optional[PDFContentScope] = None):
    """Decorator to register a preprocessing step for a specific content source.

    Args:
        source (PDFContentSource): The content source element (text, table, image)
        scope (Optional[PDFContentScope], optional): The content scope (line, paragraph, page).
                                                     Defaults to None. Required for text elements.

    Raises:
        PreprocessingError: If the scope is not specified for text elements.

    Note:
        When you decorate a function with this decorator, the function will be called on each
        element of the specified type (text, table, image) during the preprocessing step
        (in order of registration). If the content source is text, you must also specify the
        content scope (line, paragraph, page). Then the function will be called only on elements
        of that type (e.g. line) during the preprocessing step.
    """

    def decorator(func):
        # Register the preprocessor depending on the content source and scope
        if source == PDFContentSource.TEXT:
            if scope is None:
                raise PreprocessingError("For text elements, you must specify a content scope.")
            _preprocessors[source][scope].append(func)
        else:
            _preprocessors[source].append(func)
        return func

    return decorator
