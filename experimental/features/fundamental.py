def extract_fundamentals(raw: dict) -> dict:
    return {
        'pe_ratio': float(raw.get('PERatio') or 0.0),
        'eps': float(raw.get('EPS') or 0.0),
        'revenue_ttm': float(raw.get('RevenueTTM') or 0.0),
    }
