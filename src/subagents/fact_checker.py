from typing import TypedDict, List, Dict, Annotated
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
import operator
import json

# Initialize LLM
# llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0)
from langchain_community.chat_models import FakeListChatModel
llm = FakeListChatModel(responses=['["Claim 1", "Claim 2"]', "True: Verified", "False: Debunked"])

class FactCheckState(TypedDict):
    claims: List[str]
    evidence: Dict[str, List[str]]
    verdicts: Dict[str, str]
    final_report: str

def claim_extractor(state: FactCheckState):
    """Extracts claims from the input using an LLM."""
    print("--- FactChecker: Extracting Claims ---")
    # We assume the input query is implicitly available or passed in a way we can access.
    # For this subagent, we might need to adjust the state to include the original query if not present.
    # Assuming 'claims' might be empty initially and we extract from a 'query' field if we added it,
    # but strictly following the current state, we might be extracting from the last message if connected to main graph.
    # For now, let's assume the input state has a 'query' or we extract from context.
    # Let's add 'query' to FactCheckState for clarity in a real impl, but for now we mock the input source.
    
    # In a real integration, we'd pass the query. Let's assume it's passed in 'claims' as a single string initially?
    # Or better, let's just use a fixed prompt for now if we can't change the state definition easily without breaking others.
    # Actually, we can just change the node logic.
    
    # Let's assume the first item in 'claims' is the text to check if it's a raw string, 
    # or we need to update the State definition.
    # Let's update the State definition in a separate step if needed, but here we'll just use a placeholder 
    # or assume the 'claims' list is populated by the caller (the router/main graph).
    
    # If the main graph passes the query as a claim, we refine it.
    raw_text = state['claims'][0] if state['claims'] else "No text provided"
    
    prompt = ChatPromptTemplate.from_template(
        "Extract distinct factual claims from the following text. Return them as a JSON list of strings.\nText: {text}"
    )
    chain = prompt | llm | JsonOutputParser()
    
    try:
        claims = chain.invoke({"text": raw_text})
    except:
        claims = [raw_text] # Fallback
        
    return {"claims": claims}

def evidence_search(state: FactCheckState):
    """Searches for evidence for each claim."""
    claims = state['claims']
    evidence = {}
    print(f"--- FactChecker: Searching Evidence for {len(claims)} claims ---")
    
    for claim in claims:
        # Mock search
        evidence[claim] = [f"Source A says about '{claim}'...", f"Source B says..."]
        
    return {"evidence": evidence}

def verifier(state: FactCheckState):
    """Verifies claims based on evidence using an LLM."""
    claims = state['claims']
    evidence = state['evidence']
    verdicts = {}
    print("--- FactChecker: Verifying Claims ---")
    
    for claim in claims:
        claim_evidence = evidence.get(claim, [])
        evidence_str = "\n".join(claim_evidence)
        
        prompt = ChatPromptTemplate.from_template(
            """Verify the following claim based on the evidence provided.
            Claim: {claim}
            Evidence:
            {evidence}
            
            Return a verdict (True/False/Unverified) and a brief explanation.
            Format: Verdict: Explanation"""
        )
        chain = prompt | llm | StrOutputParser()
        verdict = chain.invoke({"claim": claim, "evidence": evidence_str})
        verdicts[claim] = verdict
            
    return {"verdicts": verdicts}

def report_generator(state: FactCheckState):
    """Generates the final fact check report."""
    verdicts = state['verdicts']
    report = "# Fact Check Report\n\n"
    for claim, verdict in verdicts.items():
        report += f"- **Claim**: {claim}\n  - **Verdict**: {verdict}\n"
        
    return {"final_report": report}

# Build Subgraph
workflow = StateGraph(FactCheckState)
workflow.add_node("extractor", claim_extractor)
workflow.add_node("searcher", evidence_search)
workflow.add_node("verifier", verifier)
workflow.add_node("reporter", report_generator)

workflow.set_entry_point("extractor")
workflow.add_edge("extractor", "searcher")
workflow.add_edge("searcher", "verifier")
workflow.add_edge("verifier", "reporter")
workflow.add_edge("reporter", END)

fact_checker_app = workflow.compile()
