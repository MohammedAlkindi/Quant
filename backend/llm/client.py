from anthropic import Anthropic

from backend.config import get_settings
from backend.llm.prompts import SYSTEM_PROMPT, build_user_prompt


class ClaudeClient:
    def __init__(self):
        settings = get_settings()
        self.model = settings.claude_model
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def analyze(self, context: dict) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': build_user_prompt(context)}],
        )
        return message.content[0].text
