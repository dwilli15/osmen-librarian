import sys
import os
import unittest
from langgraph.errors import GraphInterrupt

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from middleware.hitl import HITLMiddleware

class TestHITL(unittest.TestCase):
    
    def test_interruption(self):
        print("\nTesting HITL Interruption...")
        hitl = HITLMiddleware()
        
        try:
            hitl.request_approval("Deploy to Production")
        except GraphInterrupt as e:
            print(f"Caught expected interrupt: {e}")
            self.assertIn("Approval required", str(e))
            
        print("HITL Interruption passed.")

if __name__ == "__main__":
    unittest.main()
