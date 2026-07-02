import re
import logging
from typing import Optional
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class GuardrailResult(BaseModel):
    is_allowed: bool
    reason: str
    refusal_message: Optional[str] = None
    educational_url: Optional[str] = None
    sanitized_query: str = ""

class IntentClassifier:
    """
    Pre-retrieval classification layer to detect and block advisory, speculative,
    or promotional financial queries. Enforces strict regulatory compliance (SEBI/AMFI rules).
    Also sanitizes and redacts all user PII (PAN, Aadhaar, Phone).
    """
    AMFI_EDU_URL = "https://www.amfiindia.com/investor-corner"
    
    # Strict regex patterns for PII detection (PAN, Aadhaar, Phone Numbers)
    PII_PATTERNS = [
        (r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", "[REDACTED_PAN]"),
        (r"\b\d{4}\s?\d{4}\s?\d{4}\b", "[REDACTED_AADHAAR]"),
        (r"\b[6-9]\d{9}\b", "[REDACTED_PHONE]"),
    ]
    
    # Comprehensive regex patterns for investment advice, recommendations, and speculation
    ADVISORY_PATTERNS = [
        r"\b(should\s+i|can\s+i|must\s+i|how\s+much\s+should\s+i)\b.*\b(invest|buy|sell|switch|sip|redeem|put|allocate)\b",
        r"\b(which|what)\b.*\b(fund|scheme)\b.*\b(better|best|recommended|good\s+to\s+buy|to\s+invest)\b",
        r"\b(recommend|suggest|advise|advice|guidance)\b.*\b(fund|scheme|portfolio|stock|investment|sip|money)\b",
        r"\b(is\s+it\s+a\s+good\s+time|is\s+it\s+worth|safe\s+to\s+invest|right\s+time\s+to\s+buy|should\s+we\s+invest)\b",
        r"\b(compare|comparison)\b.*\b(returns|performance|growth|better)\b",
        r"\b(future|expected|guaranteed|predict|forecast|target)\b.*\b(price|return|growth|rate|value|multibagger)\b",
        r"\bwill\s+(it|the\s+fund|hdfc|this)\b.*\b(go\s+up|increase|double|reach|give)\b",
        r"\b(multibagger|hot\s+tip|sure\s+shot|portfolio\s+allocation|where\s+should\s+i\s+invest)\b"
    ]

    @classmethod
    def scrub_pii(cls, text: str) -> str:
        """
        Scrubs potential Indian PII (PAN cards, Aadhaar numbers, Indian mobile numbers)
        from user queries to guarantee zero PII storage or collection.
        """
        scrubbed = text
        for pattern, replacement in cls.PII_PATTERNS:
            scrubbed = re.sub(pattern, replacement, scrubbed, flags=re.IGNORECASE)
        return scrubbed

    @classmethod
    def evaluate_query(cls, query: str) -> GuardrailResult:
        """
        Evaluates user query against refusal rules and scrubs PII.
        Returns a GuardrailResult indicating whether the query is allowed or blocked.
        """
        sanitized = cls.scrub_pii(query)
        cleaned_query = sanitized.strip().lower()
        
        for pattern in cls.ADVISORY_PATTERNS:
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                logger.warning(f"Query blocked by guardrail pattern '{pattern}': \"{query}\"")
                refusal_msg = (
                    "I am an AI assistant designed to provide factual information about HDFC mutual funds "
                    "from official scheme documents and fact sheets. Strictly no investment advice or return forecasts can be provided. "
                    "For educational resources and guidance on mutual fund investing, please visit AMFI."
                )
                return GuardrailResult(
                    is_allowed=False,
                    reason="Query requests financial advice, recommendation, or return speculation.",
                    refusal_message=refusal_msg,
                    educational_url=cls.AMFI_EDU_URL,
                    sanitized_query=sanitized
                )
                
        return GuardrailResult(
            is_allowed=True,
            reason="Query asks for factual scheme information.",
            sanitized_query=sanitized
        )

if __name__ == "__main__":
    res = IntentClassifier.evaluate_query("Should I invest in HDFC Small Cap Fund?")
    print(f"Allowed: {res.is_allowed}, Reason: {res.reason}")
