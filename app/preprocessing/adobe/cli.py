import os
import pathlib
from argparse import ArgumentParser, FileType

from dotenv import load_dotenv

from app.preprocessing.adobe.exceptions import AdobeExtractAPIInvalidFileError
from app.preprocessing.adobe.manager import AdobeExtractAPIManager


def main(args):
    # Initialize Adobe Extract API Manager
    manager = AdobeExtractAPIManager(
        client_id=os.getenv("ADOBE_CLIENT_ID"),
        client_secret=os.getenv("ADOBE_CLIENT_SECRET"),
        extract_dir_path=args.out,
    )

    for file in args.file:
        try:
            # Extract PDF
            _ = manager.get_document(file)

            print(f"Done with {file}")
        except AdobeExtractAPIInvalidFileError:
            print(f"File {file} couldn't be processed with Adobe Extract API. skipping...")


if __name__ == "__main__":
    # Get cur dir
    cur_dir = pathlib.Path(__file__).parent.resolve()

    # Get Args
    parser = ArgumentParser(description="CLI for Adobe Extract API")
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        default=cur_dir / "../../../data/interim/000-adobe-extract",
        help="Path to the directory where the extracted PDFs will be stored.",
    )
    parser.add_argument("file", type=str, nargs="+", help="Path to the file(s) to be extracted.")
    args = parser.parse_args()

    # Load .env
    load_dotenv()

    main(args)
