from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class AssistantConfig(BaseModel):
    """Configuration for an AI Assistant."""
    id: str = Field(..., description="Unique identifier for the assistant")
    name: str = Field(..., description="Human-readable name")
    model: str = Field("gpt-4o", description="Model to use")
    tools: List[str] = Field(default_factory=list, description="List of enabled middleware/tools")
    system_prompt: str = Field(..., description="System prompt for the assistant")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata")
