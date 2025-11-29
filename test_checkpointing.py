import sys
import os
import unittest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.base import CheckpointTuple

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from graph import app
from memory.checkpoint import InMemorySaver

class TestCheckpointing(unittest.TestCase):
    
    def test_persistence(self):
        print("\nTesting Checkpointing...")
        
        # 1. Start a conversation
        config = {"configurable": {"thread_id": "thread-1"}}
        inputs = {"messages": [HumanMessage(content="Hello, remember this.")]}
        
        print("--- Step 1: Initial Interaction ---")
        for output in app.stream(inputs, config=config):
            pass
            
        # 2. Verify state is saved
        state = app.get_state(config)
        print(f"Saved State: {state.values.get('messages')}")
        self.assertTrue(len(state.values['messages']) > 0)
        
        # 3. Continue conversation (Resume)
        print("--- Step 2: Resume Conversation ---")
        inputs_2 = {"messages": [HumanMessage(content="What did I just say?")]}
        for output in app.stream(inputs_2, config=config):
            pass
            
        # 4. Verify history is preserved
        state_2 = app.get_state(config)
        messages = state_2.values['messages']
        print(f"Final History Length: {len(messages)}")
        self.assertTrue(len(messages) >= 3) # User + AI + User + AI (at least)
        
        print("Checkpointing tests passed.")

if __name__ == "__main__":
    unittest.main()
