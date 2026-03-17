SYSTEM_PROMPT = """You are Quant's trading copilot. Provide concise, risk-aware analysis.
Always include recommendation (BUY/SELL/HOLD), confidence (0-1), and reasoning bullets.
"""


def build_user_prompt(context: dict) -> str:
    return (
        'Analyze the following market context as JSON and respond with\n'
        '{"recommendation":"BUY|SELL|HOLD","confidence":0-1,"reasoning":[...]}\n\n'
        f'context={context}'
    )
