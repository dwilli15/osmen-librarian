from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import operator

# Initialize LLM
# llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0)
from langchain_community.chat_models import FakeListChatModel
llm = FakeListChatModel(responses=['["Research Step 1", "Research Step 2"]', "Search Result 1", "Search Result 2", "Final Report"])

# Import RAG logic
try:
    from rag_manager import query_knowledge_base
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from rag_manager import query_knowledge_base

class DeepResearchState(TypedDict):
    original_query: str
    plan: List[str]
    research_results: Annotated[List[str], operator.add]
    final_report: str

def planner_node(state: DeepResearchState):
    """Generates a research plan using an LLM."""
    query = state['original_query']
    print(f"--- Deep Research: Planning '{query}' ---")
    
    prompt = ChatPromptTemplate.from_template(
        """You are a research planner. Break down the following query into a list of 3-5 distinct research steps/questions.
        Return a JSON list of strings.
        Query: {query}"""
    )
    chain = prompt | llm | JsonOutputParser()
    
    try:
        plan = chain.invoke({"query": query})
    except:
        plan = [f"Research {query}"]
        
    return {"plan": plan}

def executor_node(state: DeepResearchState):
    """Executes the research plan using an LLM (Simulated Search)."""
    plan = state['plan']
    results = []
    print(f"--- Deep Research: Executing {len(plan)} steps ---")
    
    # In a real integration, we would use Tavily/DuckDuckGo here.
    # For now, we simulate the search result using the LLM to hallucinate/generate "findings" 
    # or we could use the 'foundation_retrieval' if we imported it.
    
    for step in plan:
        prompt = ChatPromptTemplate.from_template(
            "Simulate a search result for the query: '{step}'. Provide a brief paragraph of factual information."
        )
        chain = prompt | llm | StrOutputParser()
        res = chain.invoke({"step": step})
        results.append(f"Step: {step}\nResult: {res}")
        
    return {"research_results": results}

def synthesizer_node(state: DeepResearchState):
    """Synthesizes the final report using an LLM."""
    query = state['original_query']
    results = state['research_results']
    print("--- Deep Research: Synthesizing ---")
    
    context = "\n\n".join(results)
    
    prompt = ChatPromptTemplate.from_template(
        """Write a comprehensive research report for the query based on the findings.
        Query: {query}
        
        Findings:
        {context}
        """
    )
    chain = prompt | llm | StrOutputParser()
    report = chain.invoke({"query": query, "context": context})
    
    return {"final_report": report}

# Build Subgraph
workflow = StateGraph(DeepResearchState)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "synthesizer")
workflow.add_edge("synthesizer", END)

deep_research_app = workflow.compile()
