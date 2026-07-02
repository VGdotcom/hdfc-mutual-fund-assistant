import pytest
import re
from rag.guardrails import IntentClassifier
from scraper.groww_scraper import GrowwScraper
from vector_store.schema import ChunkMetadata, DocumentChunk

def test_pii_scrubber_pan_card():
    raw_query = "Hello, my PAN card is ABCDE1234F and I want to know the expense ratio of HDFC Small Cap."
    scrubbed = IntentClassifier.scrub_pii(raw_query)
    assert "ABCDE1234F" not in scrubbed
    assert "[REDACTED_PAN]" in scrubbed
    assert "expense ratio of HDFC Small Cap" in scrubbed

def test_pii_scrubber_aadhaar_number():
    raw_query = "Please check my Aadhaar 1234 5678 9012 for HDFC Gold ETF returns."
    scrubbed = IntentClassifier.scrub_pii(raw_query)
    assert "1234 5678 9012" not in scrubbed
    assert "[REDACTED_AADHAAR]" in scrubbed

def test_pii_scrubber_phone_number():
    raw_query = "Call me at 9876543210 regarding exit load."
    scrubbed = IntentClassifier.scrub_pii(raw_query)
    assert "9876543210" not in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed

def test_zero_pii_in_metadata_schema():
    # Verify that ChunkMetadata schema contains NO fields capable or intended for storing user PII
    schema_fields = ChunkMetadata.model_fields.keys()
    pii_forbidden = ["pan", "aadhaar", "phone", "email", "account", "otp", "user_id"]
    for field in schema_fields:
        for forbidden in pii_forbidden:
            assert forbidden not in field.lower(), f"Forbidden PII field '{field}' detected in schema!"

def test_guardrails_eval_applies_pii_scrubbing():
    query_with_pii = "My PAN is ABCDE1234F, what is the exit load for HDFC Mid Cap?"
    res = IntentClassifier.evaluate_query(query_with_pii)
    # The query is allowed (it asks for exit load), but the scrubbed query should be sanitized
    assert res.is_allowed is True
    assert "ABCDE1234F" not in res.sanitized_query
    assert "[REDACTED_PAN]" in res.sanitized_query
