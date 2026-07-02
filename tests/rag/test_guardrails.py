import pytest
from rag.guardrails import IntentClassifier, GuardrailResult

def test_allowed_factual_queries():
    allowed_queries = [
        "What is the expense ratio of HDFC Small Cap Fund?",
        "Who is the fund manager for HDFC Gold ETF?",
        "What is the minimum SIP amount for HDFC Mid Cap Fund Direct Growth?",
        "What is the exit load structure of HDFC Nifty 50 Index Fund?",
        "Tell me the investment objective of HDFC Flexi Cap Fund."
    ]
    for q in allowed_queries:
        res = IntentClassifier.evaluate_query(q)
        assert res.is_allowed is True, f"Factual query should be allowed: {q}"
        assert res.refusal_message is None
        assert res.educational_url is None

def test_blocked_advisory_queries():
    blocked_queries = [
        "Should I invest in HDFC Small Cap Fund right now?",
        "Which fund is better: HDFC Mid Cap or HDFC Flexi Cap?",
        "Recommend a good mutual fund for my retirement in 10 years.",
        "Will HDFC Gold ETF go up by 15% next year?",
        "Is it a good time to buy HDFC Small Cap?",
        "Please suggest a scheme where I should put money.",
        "Compare returns between HDFC Nifty 50 and HDFC Mid Cap."
    ]
    for q in blocked_queries:
        res = IntentClassifier.evaluate_query(q)
        assert res.is_allowed is False, f"Advisory query should be blocked: {q}"
        assert res.refusal_message is not None
        assert "Strictly no investment advice" in res.refusal_message or "factual information" in res.refusal_message
        assert res.educational_url == "https://www.amfiindia.com/investor-corner"
