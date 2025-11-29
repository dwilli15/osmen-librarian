import sys
import os
from langchain_core.messages import HumanMessage

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from graph import app

def test_graph():
    print("=== Testing LangGraph Agent ===")
    
    # Test 1: Foundation Query
    print("\n[Test 1] Foundation Query ('What is Python?')")
    inputs = {"messages": [HumanMessage(content="What is Python?")]}
    config = {"configurable": {"thread_id": "test_thread_1"}}
    for output in app.stream(inputs, config=config):
        for key, value in output.items():
            print(f"Node '{key}': {value.keys()}")
            if key == "responder":
                print(f"Answer: {value['answer'][:100]}...")

    # Test 2: Lateral Query
    print("\n[Test 2] Lateral Query ('Connect Python to biology laterally')")
    inputs = {"messages": [HumanMessage(content="Connect Python to biology laterally")]}
    config = {"configurable": {"thread_id": "test_thread_2"}}
    for output in app.stream(inputs, config=config):
        for key, value in output.items():
            print(f"Node '{key}': {value.keys()}")
            if key == "router":
                print(f"Router Decision: {value['mode']}")
            if key == "responder":
                print(f"Answer: {value['answer'][:100]}...")

    # Test 3: Deep Research
    print("\n[Test 3] Deep Research ('Plan a research on AI agents')")
    inputs = {"messages": [HumanMessage(content="Plan a research on AI agents")]}
    config = {"configurable": {"thread_id": "test_thread_3"}}
    for output in app.stream(inputs, config=config):
        for key, value in output.items():
            print(f"Node '{key}': {value.keys()}")
            if key == "router":
                print(f"Router Decision: {value['mode']}")
            if key == "deep_research":
                print(f"Final Report: {value['answer'][:100]}...")

if __name__ == "__main__":
    test_graph()
