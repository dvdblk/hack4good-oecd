from langchain.document_loaders import TextLoader
from langchain.schema.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def get_standard_doc_splits(file_path, chunk_size=2000, chunk_overlap=0):
    loader = TextLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    all_splits = text_splitter.split_documents(documents)
    return all_splits