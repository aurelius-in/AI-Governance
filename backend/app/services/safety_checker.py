import re
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()


class SafetyResult:
    def __init__(self, safe: bool, violation_type: Optional[str] = None, details: Dict[str, Any] = None):
        self.safe = safe
        self.violation_type = violation_type
        self.details = details or {}


class SafetyChecker:
    def __init__(self):
        # PII patterns
        self.pii_patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        }
        
        # Toxic keywords
        self.toxic_keywords = [
            "hate", "violence", "discrimination", "harassment", "abuse",
            "threat", "kill", "murder", "suicide", "bomb", "terrorist"
        ]
        
        # Jailbreak patterns
        self.jailbreak_patterns = [
            r"ignore.*previous.*instructions",
            r"forget.*rules",
            r"act.*as.*if",
            r"pretend.*to.*be",
            r"system.*prompt",
            r"ignore.*safety"
        ]

    async def check_input(self, messages: Optional[List[Dict[str, Any]]] = None, prompt: Optional[str] = None, user_id: int = None) -> SafetyResult:
        """Check input for safety violations"""
        
        content = ""
        if messages:
            content = " ".join([msg.get("content", "") for msg in messages])
        elif prompt:
            content = prompt
        
        # Check for PII
        pii_result = self._check_pii(content)
        if not pii_result.safe:
            return pii_result
        
        # Check for toxicity
        toxicity_result = self._check_toxicity(content)
        if not toxicity_result.safe:
            return toxicity_result
        
        # Check for jailbreak attempts
        jailbreak_result = self._check_jailbreak(content)
        if not jailbreak_result.safe:
            return jailbreak_result
        
        return SafetyResult(safe=True)

    async def check_output(self, content: str, user_id: int = None) -> SafetyResult:
        """Check output for safety violations"""
        
        # Check for PII in output
        pii_result = self._check_pii(content)
        if not pii_result.safe:
            return pii_result
        
        # Check for toxicity in output
        toxicity_result = self._check_toxicity(content)
        if not toxicity_result.safe:
            return toxicity_result
        
        return SafetyResult(safe=True)

    def _check_pii(self, content: str) -> SafetyResult:
        """Check for PII in content"""
        found_pii = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_pii.append({
                    "type": pii_type,
                    "count": len(matches),
                    "examples": matches[:3]  # Show first 3 examples
                })
        
        if found_pii:
            return SafetyResult(
                safe=False,
                violation_type="pii_detected",
                details={"pii_types": found_pii}
            )
        
        return SafetyResult(safe=True)

    def _check_toxicity(self, content: str) -> SafetyResult:
        """Check for toxic content"""
        content_lower = content.lower()
        found_toxic = []
        
        for keyword in self.toxic_keywords:
            if keyword in content_lower:
                found_toxic.append(keyword)
        
        if found_toxic:
            return SafetyResult(
                safe=False,
                violation_type="toxicity_detected",
                details={"toxic_keywords": found_toxic}
            )
        
        return SafetyResult(safe=True)

    def _check_jailbreak(self, content: str) -> SafetyResult:
        """Check for jailbreak attempts"""
        content_lower = content.lower()
        found_jailbreak = []
        
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, content_lower):
                found_jailbreak.append(pattern)
        
        if found_jailbreak:
            return SafetyResult(
                safe=False,
                violation_type="jailbreak_attempt",
                details={"jailbreak_patterns": found_jailbreak}
            )
        
        return SafetyResult(safe=True)

    async def redact_pii(self, content: str) -> str:
        """Redact PII from content"""
        redacted_content = content
        
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type == "email":
                redacted_content = re.sub(pattern, "[EMAIL]", redacted_content)
            elif pii_type == "phone":
                redacted_content = re.sub(pattern, "[PHONE]", redacted_content)
            elif pii_type == "ssn":
                redacted_content = re.sub(pattern, "[SSN]", redacted_content)
            elif pii_type == "credit_card":
                redacted_content = re.sub(pattern, "[CREDIT_CARD]", redacted_content)
            elif pii_type == "ip_address":
                redacted_content = re.sub(pattern, "[IP_ADDRESS]", redacted_content)
        
        return redacted_content
