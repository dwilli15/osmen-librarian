from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize LLM
# llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0)
from langchain_community.chat_models import FakeListChatModel
llm = FakeListChatModel(responses=["Executive Summary"])

class SummarizerState(TypedDict):
    content: List[str]
    summary: str

def summarizer_node(state: SummarizerState):
    """Summarizes a list of content items using an LLM."""
    content = state['content']
    print(f"--- Summarizer: Processing {len(content)} items ---")
    
    text_to_summarize = "\n\n".join(content)
    
    prompt = ChatPromptTemplate.from_template(
        """Create a concise executive summary of the following content.
        Content:
        {text}
        """
    )
    chain = prompt | llm | StrOutputParser()
    summary = chain.invoke({"text": text_to_summarize})
        
    return {"summary": summary}

workflow = StateGraph(SummarizerState)
workflow.add_node("summarize", summarizer_node)
workflow.set_entry_point("summarize")
workflow.add_edge("summarize", END)

summarizer_app = workflow.compile()
