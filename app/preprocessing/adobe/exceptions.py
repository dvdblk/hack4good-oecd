"""Exceptions related to handling Adobe Extract API and related files."""


class AdobeExtractAPIManagerError(Exception):
    """Base class for exceptions related to Adobe Extract API manager."""

    pass


class AdobeExtractAPIInvalidCredentialsError(AdobeExtractAPIManagerError):
    """Exception raised when the Adobe Extract API credentials are invalid."""

    pass


class AdobeExtractAPIInvalidFileError(AdobeExtractAPIManagerError):
    """Exception raised when the Adobe Extract API receives an invalid file.
    (Or a file that it cannot process)
    """

    pass


class AdobeExtractAPIOutOfQuotaError(AdobeExtractAPIManagerError):
    """Exception raised when the Adobe Extract API is out of quota.
    (currently 500 document tokens/month)
    """

    pass


class AdobeExtractAPIServiceError(AdobeExtractAPIManagerError):
    """Generic exception raised when the Adobe Extract API sends an error response."""

    pass
