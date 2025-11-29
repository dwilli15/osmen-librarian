from typing import TypedDict, Annotated, Sequence, Literal, List, Optional, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langsmith import traceable
import operator

# Import modes and subgraph
try:
    from modes.foundation import foundation_retrieval, foundation_response
    from modes.lateral import lateral_retrieval, lateral_response
    from deep_research import deep_research_app
    from middleware.filesystem import FilesystemMiddleware
    from middleware.todo import TodoListMiddleware
    from middleware.subagent import SubAgentMiddleware
    from middleware.hitl import HITLMiddleware
    from memory.checkpoint import InMemorySaver
    from langchain.chat_models import init_chat_model
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from modes.foundation import foundation_retrieval, foundation_response
    from modes.lateral import lateral_retrieval, lateral_response
    from deep_research import deep_research_app
    from middleware.filesystem import FilesystemMiddleware
    from middleware.todo import TodoListMiddleware
    from middleware.subagent import SubAgentMiddleware
    from middleware.hitl import HITLMiddleware
    from memory.checkpoint import InMemorySaver
    from langchain.chat_models import init_chat_model
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

# Initialize LLM
# In production, this would come from config/env
# llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0)
from langchain_community.chat_models import FakeListChatModel
llm = FakeListChatModel(responses=["foundation", "This is a mocked response."])

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    query: str
    mode: Literal["foundation", "lateral", "deep_research", "factcheck"]
    documents: List[Any] # List of dicts or Documents
    answer: str
    # Future fields from plan
    # context7: Context7 
    # active_subagent: Optional[str]
    # todos: List[str]
    # error: Optional[str]

# --- Nodes ---

@traceable
def router_node(state: AgentState):
    # Handle potential list content (e.g. multimodal)
    content = state['messages'][-1].content
    if isinstance(content, list):
        # Join text parts if it's a list of blocks
        last_msg = " ".join([c.get('text', '') for c in content if c.get('type') == 'text'])
    else:
        last_msg = str(content)
    
    system_prompt = """You are a routing assistant. Classify the user's query into one of the following modes:
    - 'lateral': For queries asking to connect unrelated concepts, find intersections, or use lateral thinking.
    - 'factcheck': For queries asking to verify a claim, check facts, or debunk myths.
    - 'deep_research': For complex queries requiring a plan, multi-step research, or deep dive.
    - 'foundation': For standard information retrieval, questions about specific topics, or general Q&A.
    
    Return ONLY the mode name (lateral, factcheck, deep_research, foundation)."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    try:
        mode = chain.invoke({"query": last_msg}).strip().lower()
        # Fallback for safety
        if mode not in ["lateral", "factcheck", "deep_research", "foundation"]:
            mode = "foundation"
    except Exception as e:
        print(f"Router LLM failed: {e}. Falling back to heuristic.")
        # Fallback heuristic
        if "lateral" in last_msg.lower() or "connect" in last_msg.lower():
            mode = "lateral"
        elif "fact" in last_msg.lower() or "check" in last_msg.lower():
            mode = "factcheck"
        elif "research" in last_msg.lower() or "plan" in last_msg.lower():
            mode = "deep_research"
        else:
            mode = "foundation"

    return {"mode": mode, "query": last_msg}

@traceable
def retrieval_node(state: AgentState):
    """Retrieves documents based on the selected mode."""
    mode = state['mode']
    query = state['query']
    
    docs = []
    if mode == "foundation":
        docs = foundation_retrieval(query)
    elif mode == "lateral":
        docs = lateral_retrieval(query)
    elif mode == "factcheck":
        # Placeholder for factcheck subagent/mode
        docs = foundation_retrieval(query) # Fallback
        
    return {"documents": docs}

@traceable
def deep_research_node(state: AgentState):
    """Invokes the Deep Research subgraph."""
    query = state['query']
    print(f"--- Node: Deep Research ({query}) ---")
    
    # Invoke subgraph
    inputs = {"original_query": query}
    result = deep_research_app.invoke(inputs)
    
    final_report = result.get("final_report", "No report generated.")
    return {"answer": final_report, "messages": [AIMessage(content=final_report)]}

@traceable
def response_node(state: AgentState):
    """Synthesizes an answer using an LLM."""
    docs = state['documents']
    mode = state['mode']
    query = state['query']
    
    # Format context
    context_str = ""
    for i, doc in enumerate(docs):
        context_str += f"Document {i+1}:\n{doc.get('content', '')}\n"
        if 'metadata' in doc:
            context_str += f"Metadata: {doc['metadata']}\n"
        context_str += "---\n"

    if not context_str:
        context_str = "No relevant documents found."

    system_prompt = """You are the Librarian Agent. Answer the user's query based on the provided context.
    Mode: {mode}
    
    If the mode is 'lateral', emphasize connections and novel intersections.
    If the mode is 'foundation', provide a comprehensive and grounded answer.
    
    Context:
    {context}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"query": query, "context": context_str, "mode": mode})

    return {"answer": answer, "messages": [AIMessage(content=answer)]}

# --- Graph Construction ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("retriever", retrieval_node)
workflow.add_node("deep_research", deep_research_node)
workflow.add_node("responder", response_node)

# Set Entry Point
workflow.set_entry_point("router")

# Add Edges
workflow.add_conditional_edges(
    "router",
    lambda x: x['mode'],
    {
        "lateral": "retriever",
        "factcheck": "retriever", # Goes to retriever for now, will go to subagent later
        "foundation": "retriever",
        "deep_research": "deep_research"
    }
)
workflow.add_edge("retriever", "responder")
workflow.add_edge("deep_research", END)
workflow.add_edge("responder", END)

# --- Middleware Registration ---
# In a real app, root_dir would come from config
fs_middleware = FilesystemMiddleware(root_dir=".") 
todo_middleware = TodoListMiddleware()
subagent_middleware = SubAgentMiddleware()
hitl_middleware = HITLMiddleware()

all_tools = []
all_tools.extend(fs_middleware.register_tools())
all_tools.extend(todo_middleware.register_tools())
all_tools.extend(subagent_middleware.register_tools())
all_tools.extend(hitl_middleware.register_tools())

# Bind tools to the graph (conceptually - for now we just make them available)
# In a full ReAct agent, we would bind these to the LLM node.
# For this custom graph, we might expose them via a specific 'tool_node' or let the router decide.
# For now, we print them to confirm registration.
print(f"Registered {len(all_tools)} tools from middleware.")

# Initialize Checkpointer
checkpointer = InMemorySaver()

# Compile with checkpointer
app = workflow.compile(checkpointer=checkpointer)
