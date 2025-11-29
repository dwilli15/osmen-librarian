from langflow.custom import CustomComponent
from langflow.field_typing import Document
from typing import List, Optional
import json

# Import our LateralEngine (assuming it's in the python path or same dir)
try:
    from lateral_thinking import LateralEngine, Context7
except ImportError:
    # Fallback for when running inside Langflow where path might differ
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from lateral_thinking import LateralEngine, Context7

class LateralThinkingComponent(CustomComponent):
    display_name = "Lateral Thinking Engine"
    description = "Enriches documents with Context7 metadata or weaves retrieval results."

    def build_config(self):
        return {
            "mode": {
                "display_name": "Mode",
                "options": ["Enrichment", "Weaving"],
                "value": "Enrichment",
            },
            "input_document": {
                "display_name": "Input Document",
                "info": "Document to enrich (for Enrichment mode)",
            },
            "query_text": {
                "display_name": "Query Text",
                "info": "Text to query (for Weaving mode)",
            },
            "vector_store": {
                "display_name": "Vector Store",
                "info": "Chroma Vector Store (for Weaving mode)",
            },
        }

    def build(
        self,
        mode: str,
        input_document: Optional[Document] = None,
        query_text: Optional[str] = None,
        vector_store: Optional[object] = None,
    ) -> List[Document]:
        
        engine = LateralEngine(vector_store=vector_store)
        
        if mode == "Enrichment":
            if not input_document:
                raise ValueError("Input Document is required for Enrichment mode")
            
            enriched = engine.enrich_document(input_document)
            return [enriched]
            
        elif mode == "Weaving":
            if not query_text:
                raise ValueError("Query Text is required for Weaving mode")
            if not vector_store:
                raise ValueError("Vector Store is required for Weaving mode")
                
            results = engine.weave_results(query_text)
            return results
            
        return []
