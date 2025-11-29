from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import StateGraph, END
from lateral_thinking import LateralEngine
from rag_manager import get_vector_store
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

# Initialize LLM
# llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0.7)
from langchain_community.chat_models import FakeListChatModel
llm = FakeListChatModel(responses=['{"focus": "query", "abstract": "abstract", "relational": "relational", "temporal": "temporal"}', "Lateral Synthesis"])

class LateralState(TypedDict):
    query: str
    dimensions: Dict[str, str]
    woven_results: List[Dict]
    synthesis: str

def decomposer(state: LateralState):
    """Decomposes query into lateral dimensions using an LLM."""
    query = state['query']
    print(f"--- LateralResearcher: Decomposing '{query}' ---")
    
    # We can still use LateralEngine's logic if it uses LLM internally, 
    # or we can do it here explicitly. 
    # If LateralEngine.generate_lateral_queries is mock, we should replace it or update it.
    # Let's assume we want to control it here for Phase 7.
    
    prompt = ChatPromptTemplate.from_template(
        """Decompose the following query into 4 distinct search dimensions:
        1. Focus: The core subject.
        2. Abstract: The underlying themes or philosophy.
        3. Relational: Connected fields or analogies.
        4. Temporal: Historical or future context.
        
        Return a JSON object with keys: focus, abstract, relational, temporal.
        Query: {query}"""
    )
    chain = prompt | llm | JsonOutputParser()
    
    try:
        dimensions = chain.invoke({"query": query})
    except:
        # Fallback
        dimensions = {"focus": query, "abstract": "philosophy of " + query, "relational": "related to " + query, "temporal": "history of " + query}
    
    return {"dimensions": dimensions}

def lateral_weaver(state: LateralState):
    """Executes searches and weaves results."""
    query = state['query']
    print("--- LateralResearcher: Weaving Context ---")
    
    vector_store = get_vector_store(device="cpu")
    engine = LateralEngine(vector_store=vector_store)
    
    results = engine.weave_results(query)
    # Convert to serializable dicts
    woven = [{"content": d.page_content, "metadata": d.metadata} for d in results]
    
    return {"woven_results": woven}

def synthesizer(state: LateralState):
    """Synthesizes the woven results using an LLM."""
    results = state['woven_results']
    query = state['query']
    print("--- LateralResearcher: Synthesizing ---")
    
    context_str = ""
    for res in results:
        context_str += f"- {res.get('content', '')}\n"
        if "c7_abstract" in res.get('metadata', {}):
             context_str += f"  [Context: {res['metadata'].get('c7_abstract')}]\n"
    
    prompt = ChatPromptTemplate.from_template(
        """Perform a lateral thinking analysis on the query based on the woven context.
        Query: {query}
        
        Context:
        {context}
        
        Synthesize a response that highlights unexpected connections, novel insights, and multi-dimensional perspectives.
        """
    )
    chain = prompt | llm | StrOutputParser()
    synthesis = chain.invoke({"query": query, "context": context_str})
             
    return {"synthesis": synthesis}

# Build Subgraph
workflow = StateGraph(LateralState)
workflow.add_node("decomposer", decomposer)
workflow.add_node("weaver", lateral_weaver)
workflow.add_node("synthesizer", synthesizer)

workflow.set_entry_point("decomposer")
workflow.add_edge("decomposer", "weaver")
workflow.add_edge("weaver", "synthesizer")
workflow.add_edge("synthesizer", END)

lateral_researcher_app = workflow.compile()
