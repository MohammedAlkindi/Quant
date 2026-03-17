import json
import re


def parse_analysis(response_text: str) -> dict:
    match = re.search(r'\{.*\}', response_text, flags=re.DOTALL)
    if not match:
        return {'recommendation': 'HOLD', 'confidence': 0.5, 'reasoning': [response_text.strip()]}
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {'recommendation': 'HOLD', 'confidence': 0.5, 'reasoning': [response_text.strip()]}
    return {
        'recommendation': parsed.get('recommendation', 'HOLD'),
        'confidence': float(parsed.get('confidence', 0.5)),
        'reasoning': parsed.get('reasoning', []),
    }
