import json
from typing import Any, Dict, Generator, List, Optional, Sequence, Type, Union

from langchain.callbacks import get_openai_callback
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.chains.openai_functions import create_structured_output_runnable
from langchain.chat_models import ChatOpenAI
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, format_tool_to_openai_function

from app.preprocessing.adobe.model import Document, Section
from app.prompts import (
    create_summaries_prompt_template,
    refine_answer_prompt_template,
    structured_metadata_prompt_template,
)

SectionSummaryDict = Dict[str, Optional[str]]


class SectionSummaryOutput(BaseModel):
    """Contains summary of a given section"""

    summary: Optional[str] = Field(None, description="the summary of the section")


class FetchSectionsSchema(BaseModel):
    reasoning: str = Field(description="the reasoning behind the selection of a section to fetch")
    section_ids: Sequence[str] = Field(description="the exact ID(s) of the section(s) to fetch")


class FetchSectionsTool(BaseTool):
    name = "fetch_sections"
    description = "fetches an entire section or sections from a document that might contain an answer to the question"
    args_schema: Type[FetchSectionsSchema] = FetchSectionsSchema

    def _run(
        self,
        reasoning: str,
        section_ids: Sequence[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> Sequence[str]:
        """Use the tool."""
        # FIXME: can't add section_summaries to self, don't use this
        raise NotImplementedError()
        sections = []
        section_mapper = lambda s_id: self.section_summaries[s_id]

        # get full section text from document
        for section_id in sorted(section_ids):
            section = section_mapper(section_id)
            result = {"title": section.title_clean, "id": section.id, "text": section.text}
            sections.append(result)

        return sections


class RefineIO(BaseModel):
    intermediate_answer: str = Field(
        description="your previous intermediate answer that might need to be refined with the additional context"
    )
    section_ids: Sequence[str] = Field(
        description="the exact ID(s) of the sections that were used to generate the intermediate answer"
    )


class DocumentStructuredMetadata:
    def __init__(self, document: Section, section_summaries: SectionSummaryDict):
        self.value = self._create_structured_metadata(document, section_summaries)

    def _create_structured_metadata(self, section, section_summaries) -> Dict[str, Any]:
        """Convert document to structured metadata"""
        # Check if the document is the root node
        if section.section_type == "document":
            return {
                "document": {
                    "title": section.title,
                    "sections": [
                        self._create_structured_metadata(section, section_summaries)
                        for section in section.subsections
                    ],
                }
            }
        else:
            # find section from section summaries
            summary_response = section_summaries[section.id]

            result = {
                "title": section.title_clean,
                "id": section.id,
                "pages": sorted(section.pages),
                "summary": summary_response.summary,
            }
            if subsections := [
                self._create_structured_metadata(subsection, section_summaries)
                for subsection in section.subsections
            ]:
                result["sections"] = subsections

            return result


def track_costs(func):
    """Decorator that tracks OpenAI costs of OpenAIPromptExecutor methods via get_openai_callback"""

    def wrapper(self, *args, **kwargs):
        with get_openai_callback() as cb:
            result = func(self, *args, **kwargs)
            self.n_successful_requests += cb.successful_requests
            self.n_prompt_tokens += cb.prompt_tokens
            self.n_completion_tokens += cb.completion_tokens
            self.total_cost += cb.total_cost
            print(cb)
        return result

    return wrapper


def document_to_structured_metadata(section, section_summaries):
    """Convert document to structured metadata"""
    # Check if the document is the root node
    if section.section_type == "document":
        return {
            "document": {
                "title": section.title,
                "sections": [
                    document_to_structured_metadata(section, section_summaries)
                    for section in section.subsections
                ],
            }
        }
    else:
        # find section from section summaries
        section_summary = section_summaries[section.id]
        result = {
            "title": section.title_clean,
            "id": section.id,
            "pages": sorted(section.pages),
            "summary": section_summary,
        }
        if subsections := [
            document_to_structured_metadata(subsection, section_summaries)
            for subsection in section.subsections
        ]:
            result["sections"] = subsections

        return result


def parse_function_output(response, document) -> Union[List[Section], str]:
    # Get the function call
    fn_call = response.additional_kwargs.get("function_call")

    # Check if the response content is empty and that there is a function call
    if response.content == "" and fn_call is not None:
        # Get the attributes of the function call
        tool_name = fn_call["name"]
        tool_args = json.loads(fn_call["arguments"])
        # Get the correct tool from the tools list
        # tool = next(filter(lambda x: x.name == tool_name, tools))
        # fn_output = tool._run(**tool_args)

        if tool_name == "fetch_sections" and "section_ids" in tool_args:
            sections = []
            # get full section text from document
            for section_id in sorted(tool_args["section_ids"]):
                if section := document.get_section_by_id(section_id):
                    result = {
                        "title": section.title_clean,
                        "id": section.id,
                        "text": section.text,
                    }
                    sections.append(result)
        return sections
    else:
        # Otherwise return the content
        return response.content


class OpenAIPromptExecutor:
    """Executes all pre-defined prompts (chains) while keeping track of OpenAI costs."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        # Total amount of input tokens that were fed into the model
        self.n_prompt_tokens = 0
        # Total amount of output tokens that were generated by the model
        self.n_completion_tokens = 0
        # Total amount of `_generate` calls
        self.n_successful_requests = 0
        # Total cost
        self.total_cost = 0

    @track_costs
    def temp(self, question: str) -> str:
        response = self.llm.invoke(question)
        return response.content

    @track_costs
    def create_summaries_chain(
        self, sections: List[Section]
    ) -> Generator[float, List[Section], None]:
        """Create summaries for all sections in the document

        Args:
            sections (List[Section]): the sections to summarize

        Returns:
            Generator: yields a dictionary containing the summaries for each section id
        """

        # key = section id, value = summary
        summary_dict = {}

        # create the runnable
        summary_runnable = create_structured_output_runnable(
            SectionSummaryOutput, self.llm, create_summaries_prompt_template
        )
        # Generate summaries for each section
        i = 0
        max_i = len(sections)
        for section in sections:
            section_text = section.paragraph_text

            # Check if we need to call the API (only if text exists)
            if len(section_text) > 0:
                response = summary_runnable.invoke(
                    {"section_title": section.title_clean, "section_text": section_text}
                )
                summary_dict[section.id] = response.summary
            else:
                summary_dict[section.id] = None

            i += 1
            yield (i / max_i, summary_dict)

    @track_costs
    def generic_question_chain(
        self,
        document: Document,
        section_summaries: SectionSummaryDict,
        question: str,
    ):
        # Create langchain tools
        tools = [
            FetchSectionsTool(section_summaries=section_summaries),
        ]
        # Transform to openai functions
        openai_functions = [format_tool_to_openai_function(t) for t in tools]

        fetch_sections_response = self.llm.invoke(
            structured_metadata_prompt_template.format(
                question=question,
                document_structural_metadata=document_to_structured_metadata(
                    document, section_summaries
                ),
            ),
            functions=openai_functions,
        )

        # Refine all sections into one answer if there are more than 1 section returned by the chain above
        fetched_sections = parse_function_output(fetch_sections_response, document)
        if isinstance(fetched_sections, list):
            if len(fetched_sections) == 0:
                # No sections were fetched by LLM, return generic response
                return RefineIO(
                    intermediate_answer="The answer could not be determined from the given context and question 😓",
                    section_ids=[],
                )
        elif isinstance(fetched_sections, str):
            # LLM returned an unexpected response.content (should have been null + function call but wasn't)
            return RefineIO(
                intermediate_answer=fetched_sections,
                section_ids=[],
            )
        print(fetched_sections)
        refine_io = RefineIO(intermediate_answer="", section_ids=[])
        refine_answer_runnable = create_structured_output_runnable(
            RefineIO, self.llm, refine_answer_prompt_template
        )

        for section in fetched_sections:
            refine_io = refine_answer_runnable.invoke(
                {"refine_io": refine_io.json(), "section": section, "question": question}
            )

        return refine_io
