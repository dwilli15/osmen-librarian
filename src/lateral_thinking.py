import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from langchain_core.documents import Document

@dataclass
class Context7:
    """
    The 7-Dimensional Context Model.
    Represents the '4D' impact woven through data and workflow.
    """
    intent: str = ""        # 1. Direct user goal
    domain: str = ""        # 2. Subject matter field
    emotion: str = ""       # 3. Tone and sentiment
    temporal: str = ""      # 4. Time-based relevance
    spatial: str = ""       # 5. Location/Environment
    relational: str = ""    # 6. Social/Interpersonal dynamics
    abstract: str = ""      # 7. Metaphorical/Lateral connections

    def to_metadata(self) -> Dict[str, str]:
        return {
            "c7_intent": self.intent,
            "c7_domain": self.domain,
            "c7_emotion": self.emotion,
            "c7_temporal": self.temporal,
            "c7_spatial": self.spatial,
            "c7_relational": self.relational,
            "c7_abstract": self.abstract
        }

    @classmethod
    def from_metadata(cls, meta: Dict[str, Any]) -> 'Context7':
        return cls(
            intent=meta.get("c7_intent", ""),
            domain=meta.get("c7_domain", ""),
            emotion=meta.get("c7_emotion", ""),
            temporal=meta.get("c7_temporal", ""),
            spatial=meta.get("c7_spatial", ""),
            relational=meta.get("c7_relational", ""),
            abstract=meta.get("c7_abstract", "")
        )

class LateralEngine:
    """
    Engine for injecting and retrieving lateral context.
    """
    def __init__(self, vector_store=None, embedding_function=None):
        self.vector_store = vector_store
        self.embedding_function = embedding_function

    def enrich_document(self, doc: Document) -> Document:
        """
        Enriches a document with Context7 metadata.
        In a full implementation, this would call an LLM.
        For now, we use heuristic keywords or placeholders.
        """
        try:
            if not isinstance(doc, Document):
                print(f"Warning: Expected Document, got {type(doc)}. Skipping enrichment.")
                return doc

            content = doc.page_content.lower()
            
            # Simple Heuristic Enrichment (Placeholder for LLM)
            c7 = Context7()
            
            # Domain detection
            if "python" in content or "code" in content:
                c7.domain = "technical"
            elif "philosophy" in content or "concept" in content:
                c7.domain = "philosophical"
                
            # Abstract/Lateral detection
            if "like" in content or "as if" in content:
                c7.abstract = "metaphorical"
                
            # Relational
            if "user" in content or "agent" in content:
                c7.relational = "interaction"

            # Update metadata
            doc.metadata.update(c7.to_metadata())
            return doc
        except Exception as e:
            print(f"Error enriching document: {e}")
            return doc

    def generate_lateral_queries(self, query_text: str) -> Dict[str, str]:
        """
        Generates queries for each dimension of Context7.
        """
        return {
            "focus": f"Represent this specific question for precise retrieval: {query_text}",
            "abstract": f"Represent the metaphorical and abstract implications of: {query_text}",
            "relational": f"Represent the social and interpersonal dynamics of: {query_text}",
            "temporal": f"Represent the historical or future evolution of: {query_text}"
        }

    def weave_results(self, query_text: str, k: int = 5) -> List[Document]:
        """
        Weaves results from multiple dimensions.
        """
        if not self.vector_store:
            # Fallback if no vector store (e.g. unit testing without mock)
            print("Warning: Vector store not initialized in LateralEngine.")
            return []

        try:
            queries = self.generate_lateral_queries(query_text)
            
            # 1. Focus (Primary)
            focus_results = self.vector_store.similarity_search(queries["focus"], k=k)
            
            # 2. Abstract (Lateral)
            abstract_results = self.vector_store.max_marginal_relevance_search(
                queries["abstract"], k=k, fetch_k=k*4, lambda_mult=0.4
            )
            
            # 3. Relational (Social)
            relational_results = self.vector_store.similarity_search(queries["relational"], k=k)

            # Weave: Focus, Abstract, Focus, Relational...
            woven = []
            seen = set()
            
            iterators = [
                iter(focus_results),
                iter(abstract_results),
                iter(focus_results), # Bias towards focus
                iter(relational_results)
            ]
            
            while len(woven) < k:
                added_this_round = False
                for it in iterators:
                    try:
                        doc = next(it)
                        if doc.page_content not in seen:
                            woven.append(doc)
                            seen.add(doc.page_content)
                            added_this_round = True
                        if len(woven) >= k:
                            break
                    except StopIteration:
                        continue
                
                if not added_this_round:
                    break
                    
            return woven[:k]
        except Exception as e:
            print(f"Error weaving results: {e}")
            # Fallback to simple search if weaving fails
            try:
                return self.vector_store.similarity_search(query_text, k=k)
            except:
                return []
