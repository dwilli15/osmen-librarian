import sys
import os
import unittest

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from subagents.fact_checker import fact_checker_app
from subagents.lateral_researcher import lateral_researcher_app
from subagents.summarizer import summarizer_app
from subagents.executor import executor_app

class TestSubagents(unittest.TestCase):
    
    def test_fact_checker(self):
        print("\nTesting FactChecker...")
        inputs = {"claims": [], "evidence": {}, "verdicts": {}, "final_report": ""}
        res = fact_checker_app.invoke(inputs)
        self.assertIn("Fact Check Report", res['final_report'])
        print("FactChecker passed.")

    def test_lateral_researcher(self):
        print("\nTesting LateralResearcher...")
        inputs = {"query": "Connect AI to Biology", "dimensions": {}, "woven_results": [], "synthesis": ""}
        res = lateral_researcher_app.invoke(inputs)
        self.assertIn("Lateral Analysis", res['synthesis'])
        print("LateralResearcher passed.")

    def test_summarizer(self):
        print("\nTesting Summarizer...")
        inputs = {"content": ["Item 1", "Item 2"], "summary": ""}
        res = summarizer_app.invoke(inputs)
        self.assertIn("Executive Summary", res['summary'])
        print("Summarizer passed.")

    def test_executor(self):
        print("\nTesting Executor...")
        inputs = {"task": "Run analysis", "result": ""}
        res = executor_app.invoke(inputs)
        self.assertIn("Executed", res['result'])
        print("Executor passed.")

if __name__ == "__main__":
    unittest.main()
