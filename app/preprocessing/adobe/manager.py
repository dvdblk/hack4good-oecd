import io
import json
import os.path
import zipfile
from pathlib import Path
from typing import Optional, Union

from adobe.pdfservices.operation.auth.credentials import Credentials
from adobe.pdfservices.operation.exception.exceptions import (
    ServiceApiException,
    ServiceUsageException,
)
from adobe.pdfservices.operation.execution_context import ExecutionContext
from adobe.pdfservices.operation.io.file_ref import FileRef
from adobe.pdfservices.operation.pdfops.extract_pdf_operation import ExtractPDFOperation
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_element_type import (
    ExtractElementType,
)
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_pdf_options import (
    ExtractPDFOptions,
)
from adobe.pdfservices.operation.pdfops.options.extractpdf.table_structure_type import (
    TableStructureType,
)

from app.logging import init_logger
from app.preprocessing.adobe.exceptions import (
    AdobeExtractAPIInvalidFileError,
    AdobeExtractAPIManagerError,
    AdobeExtractAPIOutOfQuotaError,
    AdobeExtractAPIServiceError,
)
from app.preprocessing.adobe.model import AdobeExtractedPDF, Document
from app.preprocessing.adobe.parser import AdobeStructuredJSONParser

logger = init_logger(__name__)


class AdobeExtractAPIManager:
    """Class for managing interaction with the Adobe Extract API."""

    def __init__(self, client_id: str, client_secret: str, extract_dir_path: str):
        """Initialize the AdobeExtractAPIManager class.

        Args:
            client_id (str): The client ID for the Adobe Extract API.
            client_secret (str): The client secret for the Adobe Extract API.
            extract_dir_path (str): The path to the directory where the extracted PDFs will be stored.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.extract_dir_path = extract_dir_path

        logger.info(
            "Initialized AdobeExtractAPIManager (with extract_dir_path=%s)", extract_dir_path
        )

    def _call_adobe_extract_api(self, input_file_stream: io.BytesIO, zip_file: str) -> str:
        """Call the Adobe Extract API to extract the PDF.

        Args:
            input_file (str): The path to the input file.
            zip_file (str): The path to the zip file where the extracted PDF will be stored.
        """
        logger.info("Calling Adobe Extract API")
        # Initial setup, create credentials instance.
        credentials = (
            Credentials.service_principal_credentials_builder()
            .with_client_id(self.client_id)
            .with_client_secret(self.client_secret)
            .build()
        )

        # Create an ExecutionContext using credentials and create a new operation instance.
        execution_context = ExecutionContext.create(credentials)
        extract_pdf_operation = ExtractPDFOperation.create_new()

        # Set operation input from a source file.
        source = FileRef.create_from_stream(input_file_stream, media_type="application/pdf")
        extract_pdf_operation.set_input(source)

        # Build ExtractPDF options and set them into the operation
        extract_pdf_options: ExtractPDFOptions = (
            ExtractPDFOptions.builder()
            .with_elements_to_extract([ExtractElementType.TEXT, ExtractElementType.TABLES])
            .with_table_structure_format(TableStructureType.CSV)
            .build()
        )
        extract_pdf_operation.set_options(extract_pdf_options)

        # Execute the operation.
        result: FileRef = extract_pdf_operation.execute(execution_context)

        # Save the result to the specified location.
        result.save_as(zip_file)

    def _process_zip_file(self, zip_file: str) -> AdobeExtractedPDF:
        """Process the zip file containing the extracted PDF."""
        # Open and read zip file
        archive = zipfile.ZipFile(zip_file, "r")
        json_data = archive.open("structuredData.json").read()
        json_data = json.loads(json_data)

        # Extract csv tables
        csv_tables = {}
        table_files = [
            file_name for file_name in archive.namelist() if file_name.startswith("tables/")
        ]

        for table_name in table_files:
            csv_tables[table_name] = (
                archive.open(table_name).read().decode("utf-8-sig").rstrip("\n")
            )

        return AdobeExtractedPDF(json_data, zip_file, csv_tables)

    def get_extracted_pdf(
        self, input_file: Union[str, bytes], input_file_name: Optional[str] = None
    ) -> AdobeExtractedPDF:
        """Get extracted PDF from Adobe Extract API (or local existing file).

        Note:
            This method will check if the extracted PDF already exists in the extract_dir_path.
            If it does, it will skip the download and return the previously extracted PDF.
            Warning: ⚠️ The check is done by comparing ONLY the filename.

            TODO: Add a check for the file hash and also
            store the file as the hash (text from first/last n pages + page count). Also remove the
            file name argument as that will no longer be needed.

        Args:
            input_file (Union[str, Path, bytes]): The input file to extract.
            input_file_name (Optional[str]): The name of the file to save the extracted PDF as.
                                        Required if input_file is bytes.
        """
        if isinstance(input_file, bytes):
            # Check if file_name is provided
            if input_file_name is None:
                raise AdobeExtractAPIManagerError(
                    "file_name must be provided if input_file is bytes."
                )
            input_basename = Path(input_file_name).stem
            input_file_stream = io.BytesIO(input_file)
        elif isinstance(input_file, str):
            input_basename = Path(input_file).stem
            input_file_stream = open(input_file, "rb")

        # Check if .zip file exists
        zip_file = os.path.join(self.extract_dir_path, f"{input_basename}.zip")

        if os.path.isfile(zip_file):
            # File already exists
            return self._process_zip_file(zip_file)
        else:
            try:
                # File does not exist, download it
                self._call_adobe_extract_api(input_file_stream, zip_file)

                # Process the zip file and return the extracted PDF
                return self._process_zip_file(zip_file)
            except ServiceApiException as e:
                if e.error_code == "BAD_PDF_DAMAGED":
                    # File could not be processed
                    raise AdobeExtractAPIInvalidFileError() from e
                else:
                    # The service returned an unexpected status code
                    raise AdobeExtractAPIServiceError(
                        f"Service returned an API error with description: {e}"
                    ) from e
            except ServiceUsageException as e:
                # Quota reached
                raise AdobeExtractAPIOutOfQuotaError(
                    f"Service returned a usage error with description: {e}"
                ) from e
            finally:
                # close the stream if needed
                if isinstance(input_file, str):
                    input_file_stream.close()

    def parse_extracted_pdf(self, adobe_extracted_pdf: AdobeExtractedPDF) -> Document:
        """Create a document from the AdobeExtractedPDF object."""
        return AdobeStructuredJSONParser().adobe_extracted_pdf_to_document(adobe_extracted_pdf)

    def get_document(
        self, input_file: Union[str, bytes], input_file_name: Optional[str] = None
    ) -> Document:
        """Convenience method for getting a document from the input file."""
        adobe_extracted_pdf = self.get_extracted_pdf(input_file, input_file_name)
        return self.parse_extracted_pdf(adobe_extracted_pdf)
