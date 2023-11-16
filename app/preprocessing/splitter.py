from typing import List

from langchain.schema import Document as LangchainDocument

from app.preprocessing.adobe.model import Document


class AdobeDocumentSplitter:
    """Create chunks from a structured document."""

    def document_to_chunks(self, document: Document) -> List[LangchainDocument]:
        """Adobe Extract API Document to LangchainDocument chunks"""
        docs = []

        # Stack of sections to process
        sections = [document]

        # While there are sections to process
        while sections:
            section = sections.pop(0)
            # Get chunk text (just join all paragraphs for now)
            chunk_content = "\n".join([p.text for p in section.paragraphs])

            # Get chunk metadata
            if section.section_type != "document":
                chunk_metadata = {section.section_type: section.title}
                parent = section.parent
                while parent is not None and parent.section_type != "document":
                    # Get section title and type
                    section_title = parent.title
                    section_type = parent.section_type
                    # e.g. { 'h1': 'Introduction' } or { 'h1': 'Introduction', 'h2': 'Skills and experience'}
                    chunk_metadata[section_type] = section_title
                    # Go up one level
                    parent = parent.parent

                # Create chunk
                chunk = LangchainDocument(page_content=chunk_content, metadata=chunk_metadata)

                # Add chunk to list of chunks
                docs.append(chunk)

            # Continue processing subsections
            for section in section.subsections:
                sections.append(section)
        return docs
