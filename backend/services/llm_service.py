from backend.llm.client import ClaudeClient
from backend.llm.parser import parse_analysis


class LLMService:
    def __init__(self):
        self.client = ClaudeClient()

    def analyze_signal(self, context: dict) -> dict:
        text = self.client.analyze(context)
        parsed = parse_analysis(text)
        return {'raw': text, 'parsed': parsed}
