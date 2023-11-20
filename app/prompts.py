"""Prompts and prompt templates"""

__all__ = ["create_summaries_prompt_template", "structured_metadata_prompt"]

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema.messages import HumanMessage, SystemMessage

_human_type_tip_message = HumanMessage(content="Tip: Make sure to answer in the correct format")

_CREATE_SUMMARIES_SYSTEM_PROMPT = """
You're an expert policy analyst that is analyzing an economic policy document. Your goal is to summarize a given section text of a document with 13-20 sentences.

The section text will be given to you in the following json format:
```json
{{
    "section": {{
        "title": "<section title>",
        "text": "<section text to summarize>"
    }}
}}
```

Make sure to follow these rules while summarizing (as if your life depended on it):
1. absolutely make sure that you don't skip any mentions of technologies, skills, capabilities or investments related to any of these topics: Advanced Computing, Battery Technologies, Semiconductors, Clean Energy.
2. pay attention to the intention of the section especially with regards to sentiment towards adoption or promotion of any skills.
3. if the text mentions or discusses policy initiatives related to inclusion, health, digital, green resilience make sure to include them in the summary.
4. mention any discussion of funding, investments or budget allocations.
5. in the summary, make sure to mention whether there is a certain future need for any skills or technologies
6. mention any explicit skill needs that are mentioned in the text.
7. if the entire section is a table of contents (e.g. line after line of headings followed by page number) just return "table of contents" as the summary
8. if the entire section contains only publication citations and nothing else, just return "references" as the summary.
9. make a shorter summary than the original section text
"""

_CREATE_SUMMARIES_INPUT_PROMPT = """
Here is the section json of a document to summarize:
```json
{{
    "section": {{
        "title": {section_title},
        "text": {section_text}
    }}
}}
```
"""


create_summaries_prompt_template = ChatPromptTemplate.from_messages(
    [
        # SystemMessage(content=_CREATE_SUMMARIES_SYSTEM_PROMPT),
        ("system", _CREATE_SUMMARIES_SYSTEM_PROMPT),
        # HumanMessage(content=_CREATE_SUMMARIES_INPUT_PROMPT),
        ("human", _CREATE_SUMMARIES_INPUT_PROMPT),
        # _human_type_tip_message,
    ]
)


# Structured metadata prompt (initial for most questions)
_STRUCTURED_METADATA_SYSTEM_PROMPT = """
You're an expert policy analyst that needs to find the appropriate sections of an economic policy document that answers the given question.
Your task is to look at the summaries in the following structural metadata json and find the appropriate section IDs of the document that might contain the answer.

Strictly adhere to these rules under all circumstances:
1. if you can't find the answer from the summaries, just fetch the most relevant sections to the question
2. for questions that are similar to "what is the document about?" or "what is the summary of the document?": try to fetch initial or final sections with "summary" or "conclusion" in their title.
3. always make sure to return all sections or subsections that might be relevant to the question as their respective IDs
"""

_STRUCTURED_METADATA_INPUT_PROMPT = """
<< Question >>
{question}

<< Document >>
{document_structural_metadata}
"""

structured_metadata_prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=_STRUCTURED_METADATA_SYSTEM_PROMPT),
        HumanMessage(content=_STRUCTURED_METADATA_INPUT_PROMPT),
    ]
)

_REFINE_ANSWER_SYSTEM_PROMPT = """
You're a world class policy analyst that is analyzing an economic policy document by going section over section. Your goal is to answer the question based on the given section text and intermediate_answer.
"""

_REFINE_ANSWER_INPUT_PROMPT = """
Here is the intermediate_answer you generated along with the section IDs that were used to generate it: \n{refine_io}
Use the given format to refine your previous intermediate_answer with the following section: \n{section}
Here is the question that you need to answer in intermediate_answer: {question}
"""

refine_answer_prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=_REFINE_ANSWER_SYSTEM_PROMPT),
        HumanMessage(content=_REFINE_ANSWER_INPUT_PROMPT),
        _human_type_tip_message,
    ]
)
