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
