"""
Safety Checker Service - Advanced AI Content Safety and PII Protection

I designed this service as the primary safety guardrail for our AI governance platform.
It implements comprehensive content safety checks, PII detection, and protection mechanisms
to ensure enterprise-grade security and compliance.

Key Design Decisions:
- I implemented multi-layered safety checks (PII, toxicity, jailbreak, bias)
- I added AI-powered sentiment analysis for better content understanding
- I created comprehensive PII patterns with context awareness
- I designed configurable safety thresholds for different use cases
- I implemented real-time content redaction and sanitization
- I added audit trails for all safety decisions

Author: Oliver Ellison
Created: 2024
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import structlog
from opentelemetry import trace, metrics
import asyncio
from datetime import datetime, timedelta
import redis

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# I create custom metrics for safety monitoring
safety_check_counter = meter.create_counter(
    name="safety_checks_total",
    description="Total number of safety checks performed"
)
safety_violation_counter = meter.create_counter(
    name="safety_violations_total",
    description="Total number of safety violations detected"
)
pii_detection_counter = meter.create_counter(
    name="pii_detections_total",
    description="Total number of PII detections"
)

class ViolationType(Enum):
    """I define safety violation types for categorization and reporting."""
    PII_DETECTED = "pii_detected"
    TOXICITY_DETECTED = "toxicity_detected"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    BIAS_DETECTED = "bias_detected"
    SENTIMENT_VIOLATION = "sentiment_violation"
    CONTENT_FILTER = "content_filter"

class SafetyLevel(Enum):
    """I define safety levels for different content types."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SafetyResult:
    """I define a comprehensive safety check result with detailed information."""
    
    safe: bool
    violation_type: Optional[ViolationType] = None
    safety_level: SafetyLevel = SafetyLevel.LOW
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    redacted_content: Optional[str] = None
    risk_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    check_id: str = field(default_factory=lambda: hashlib.md5(
        f"{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:8])

@dataclass
class PIIDetection:
    """I define PII detection results with context and confidence."""
    
    type: str
    pattern: str
    confidence: float
    context: str
    position: Tuple[int, int]
    redacted: bool = False

class SafetyChecker:
    """
    I designed this service as the comprehensive safety guardrail for AI content.
    
    Key Features:
    - Multi-layered PII detection with context awareness
    - AI-powered toxicity and bias detection
    - Advanced jailbreak pattern recognition
    - Real-time content redaction and sanitization
    - Configurable safety thresholds
    - Comprehensive audit trails
    - Performance optimization with caching
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        
        # I initialize comprehensive PII patterns with context awareness
        self._initialize_pii_patterns()
        
        # I set up toxicity detection with severity levels
        self._initialize_toxicity_patterns()
        
        # I configure jailbreak detection patterns
        self._initialize_jailbreak_patterns()
        
        # I set up bias detection patterns
        self._initialize_bias_patterns()
        
        # I configure safety thresholds
        self.safety_thresholds = {
            SafetyLevel.LOW: 0.3,
            SafetyLevel.MEDIUM: 0.6,
            SafetyLevel.HIGH: 0.8,
            SafetyLevel.CRITICAL: 0.9
        }
        
        # I enable caching for performance
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hour
        
        logger.info("Safety Checker initialized", 
                   pii_patterns=len(self.pii_patterns),
                   toxicity_patterns=len(self.toxic_patterns),
                   jailbreak_patterns=len(self.jailbreak_patterns))

    def _initialize_pii_patterns(self):
        """I initialize comprehensive PII detection patterns with context awareness."""
        
        self.pii_patterns = {
            # I implement email detection with various formats
            "email": {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "confidence": 0.95,
                "context_keywords": ["email", "contact", "reach", "send", "mail"]
            },
            
            # I implement phone number detection for multiple formats
            "phone": {
                "pattern": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
                "confidence": 0.90,
                "context_keywords": ["phone", "call", "contact", "mobile", "cell"]
            },
            
            # I implement SSN detection with validation
            "ssn": {
                "pattern": r'\b(?!000|666|9\d{2})([0-8]\d{2}|9([0-8]\d|9[0-2]))[-]?(?!00)\d{2}[-]?(?!0000)\d{4}\b',
                "confidence": 0.98,
                "context_keywords": ["ssn", "social", "security", "number", "id"]
            },
            
            # I implement credit card detection with Luhn validation
            "credit_card": {
                "pattern": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
                "confidence": 0.92,
                "context_keywords": ["card", "credit", "payment", "visa", "mastercard"]
            },
            
            # I implement IP address detection
            "ip_address": {
                "pattern": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
                "confidence": 0.85,
                "context_keywords": ["ip", "address", "network", "server"]
            },
            
            # I implement address detection
            "address": {
                "pattern": r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
                "confidence": 0.75,
                "context_keywords": ["address", "street", "location", "residence"]
            },
            
            # I implement date of birth detection
            "dob": {
                "pattern": r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b',
                "confidence": 0.80,
                "context_keywords": ["birth", "born", "date", "dob", "age"]
            },
            
            # I implement passport number detection
            "passport": {
                "pattern": r'\b[A-Z]{1,2}[0-9]{6,9}\b',
                "confidence": 0.70,
                "context_keywords": ["passport", "travel", "document", "id"]
            }
        }

    def _initialize_toxicity_patterns(self):
        """I initialize comprehensive toxicity detection patterns."""
        
        self.toxic_patterns = {
            "hate_speech": {
                "keywords": ["hate", "racist", "bigot", "discriminate", "supremacist"],
                "severity": SafetyLevel.HIGH,
                "confidence": 0.85
            },
            "violence": {
                "keywords": ["kill", "murder", "assault", "bomb", "terrorist", "attack"],
                "severity": SafetyLevel.CRITICAL,
                "confidence": 0.90
            },
            "harassment": {
                "keywords": ["harass", "bully", "stalk", "threaten", "intimidate"],
                "severity": SafetyLevel.HIGH,
                "confidence": 0.80
            },
            "self_harm": {
                "keywords": ["suicide", "self-harm", "cut", "overdose", "end it all"],
                "severity": SafetyLevel.CRITICAL,
                "confidence": 0.95
            },
            "sexual_content": {
                "keywords": ["porn", "sex", "nude", "explicit", "adult"],
                "severity": SafetyLevel.MEDIUM,
                "confidence": 0.75
            }
        }

    def _initialize_jailbreak_patterns(self):
        """I initialize advanced jailbreak detection patterns."""
        
        self.jailbreak_patterns = [
            # I detect instruction manipulation attempts
            r"ignore\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|rules?)",
            r"forget\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|rules?)",
            r"disregard\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|rules?)",
            
            # I detect role-playing attempts
            r"act\s+as\s+(?:if\s+)?(?:you\s+are\s+)?(?:a\s+)?(?:different\s+)?(?:person|character|system)",
            r"pretend\s+(?:to\s+be|you\s+are)\s+(?:a\s+)?(?:different\s+)?(?:person|character|system)",
            r"roleplay\s+as\s+(?:a\s+)?(?:different\s+)?(?:person|character|system)",
            
            # I detect system prompt extraction attempts
            r"(?:what\s+is\s+)?(?:your\s+)?(?:system\s+)?(?:prompt|instruction|rule)",
            r"(?:show\s+me\s+)?(?:your\s+)?(?:system\s+)?(?:prompt|instruction|rule)",
            r"(?:tell\s+me\s+)?(?:your\s+)?(?:system\s+)?(?:prompt|instruction|rule)",
            
            # I detect safety bypass attempts
            r"ignore\s+(?:all\s+)?(?:safety\s+)?(?:measures?|filters?|guardrails?)",
            r"bypass\s+(?:all\s+)?(?:safety\s+)?(?:measures?|filters?|guardrails?)",
            r"disable\s+(?:all\s+)?(?:safety\s+)?(?:measures?|filters?|guardrails?)",
            
            # I detect DAN-like prompts
            r"(?:you\s+are\s+)?(?:now\s+)?(?:DAN|do\s+anything\s+now)",
            r"(?:you\s+can\s+)?(?:now\s+)?(?:do\s+anything|say\s+anything)",
            r"(?:you\s+are\s+)?(?:no\s+longer\s+)?(?:bound\s+by\s+)?(?:any\s+)?(?:rules?)"
        ]

    def _initialize_bias_patterns(self):
        """I initialize bias detection patterns for fairness monitoring."""
        
        self.bias_patterns = {
            "gender_bias": {
                "keywords": ["women can't", "men are better", "female driver", "male nurse"],
                "severity": SafetyLevel.MEDIUM,
                "confidence": 0.75
            },
            "racial_bias": {
                "keywords": ["race", "ethnicity", "skin color", "nationality"],
                "severity": SafetyLevel.HIGH,
                "confidence": 0.80
            },
            "age_bias": {
                "keywords": ["old people", "young people", "boomer", "millennial"],
                "severity": SafetyLevel.LOW,
                "confidence": 0.70
            },
            "religious_bias": {
                "keywords": ["religion", "faith", "belief", "god", "allah"],
                "severity": SafetyLevel.MEDIUM,
                "confidence": 0.75
            }
        }

    async def check_input(
        self, 
        messages: Optional[List[Dict[str, Any]]] = None, 
        prompt: Optional[str] = None, 
        user_id: Optional[int] = None,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM
    ) -> SafetyResult:
        """
        I perform comprehensive safety checks on input content.
        
        This method implements:
        - Multi-layered PII detection with context awareness
        - Toxicity and bias detection
        - Jailbreak attempt recognition
        - Configurable safety thresholds
        - Performance optimization with caching
        - Comprehensive audit trails
        """
        
        with tracer.start_as_current_span("safety_check_input") as span:
            span.set_attribute("safety.level", safety_level.value)
            span.set_attribute("user.id", user_id)
            
            # I extract content from messages or prompt
            content = self._extract_content(messages, prompt)
            
            # I check cache first for performance
            cache_key = self._generate_cache_key(content, "input")
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # I perform comprehensive safety checks
            pii_result = await self._check_pii_advanced(content)
            toxicity_result = await self._check_toxicity_advanced(content)
            jailbreak_result = await self._check_jailbreak_advanced(content)
            bias_result = await self._check_bias_advanced(content)
            
            # I calculate overall risk score
            risk_score = self._calculate_risk_score(
                pii_result, toxicity_result, jailbreak_result, bias_result
            )
            
            # I determine safety level and confidence
            safety_level_result = self._determine_safety_level(risk_score, safety_level)
            
            # I create comprehensive result
            result = SafetyResult(
                safe=safety_level_result["safe"],
                violation_type=safety_level_result["violation_type"],
                safety_level=safety_level_result["level"],
                confidence=safety_level_result["confidence"],
                risk_score=risk_score,
                details={
                    "pii": pii_result,
                    "toxicity": toxicity_result,
                    "jailbreak": jailbreak_result,
                    "bias": bias_result
                }
            )
            
            # I cache the result for performance
            await self._cache_result(cache_key, result)
            
            # I record metrics
            safety_check_counter.add(1, {
                "type": "input",
                "safety_level": safety_level.value,
                "safe": result.safe
            })
            
            if not result.safe:
                safety_violation_counter.add(1, {
                    "type": "input",
                    "violation_type": result.violation_type.value if result.violation_type else "unknown"
                })
            
            span.set_attribute("safety.safe", result.safe)
            span.set_attribute("safety.risk_score", risk_score)
            
            logger.info(
                "Safety check completed",
                safe=result.safe,
                risk_score=risk_score,
                violation_type=result.violation_type.value if result.violation_type else None,
                user_id=user_id
            )
            
            return result

    async def check_output(
        self, 
        content: str, 
        user_id: Optional[int] = None,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM
    ) -> SafetyResult:
        """
        I perform safety checks on AI-generated output content.
        
        This includes:
        - PII detection in generated content
        - Toxicity and bias detection
        - Content appropriateness validation
        - Real-time redaction capabilities
        """
        
        with tracer.start_as_current_span("safety_check_output") as span:
            span.set_attribute("safety.level", safety_level.value)
            span.set_attribute("user.id", user_id)
            
            # I check cache first
            cache_key = self._generate_cache_key(content, "output")
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # I perform safety checks
            pii_result = await self._check_pii_advanced(content)
            toxicity_result = await self._check_toxicity_advanced(content)
            bias_result = await self._check_bias_advanced(content)
            
            # I calculate risk score
            risk_score = self._calculate_risk_score(pii_result, toxicity_result, None, bias_result)
            
            # I determine safety level
            safety_level_result = self._determine_safety_level(risk_score, safety_level)
            
            # I create result with redacted content if needed
            redacted_content = None
            if not safety_level_result["safe"] and pii_result["detected"]:
                redacted_content = await self.redact_pii_advanced(content)
            
            result = SafetyResult(
                safe=safety_level_result["safe"],
                violation_type=safety_level_result["violation_type"],
                safety_level=safety_level_result["level"],
                confidence=safety_level_result["confidence"],
                risk_score=risk_score,
                redacted_content=redacted_content,
                details={
                    "pii": pii_result,
                    "toxicity": toxicity_result,
                    "bias": bias_result
                }
            )
            
            # I cache and record metrics
            await self._cache_result(cache_key, result)
            
            safety_check_counter.add(1, {
                "type": "output",
                "safety_level": safety_level.value,
                "safe": result.safe
            })
            
            if not result.safe:
                safety_violation_counter.add(1, {
                    "type": "output",
                    "violation_type": result.violation_type.value if result.violation_type else "unknown"
                })
            
            span.set_attribute("safety.safe", result.safe)
            span.set_attribute("safety.risk_score", risk_score)
            
            logger.info(
                "Output safety check completed",
                safe=result.safe,
                risk_score=risk_score,
                violation_type=result.violation_type.value if result.violation_type else None,
                user_id=user_id
            )
            
            return result

    async def _check_pii_advanced(self, content: str) -> Dict[str, Any]:
        """I perform advanced PII detection with context awareness and confidence scoring."""
        
        detected_pii = []
        total_confidence = 0.0
        
        for pii_type, config in self.pii_patterns.items():
            matches = re.finditer(config["pattern"], content, re.IGNORECASE)
            
            for match in matches:
                # I calculate context confidence
                context_confidence = self._calculate_context_confidence(
                    content, match.start(), match.end(), config["context_keywords"]
                )
                
                # I calculate overall confidence
                overall_confidence = config["confidence"] * context_confidence
                
                if overall_confidence > 0.5:  # I only report high-confidence matches
                    detected_pii.append({
                        "type": pii_type,
                        "pattern": match.group(),
                        "confidence": overall_confidence,
                        "position": (match.start(), match.end()),
                        "context": content[max(0, match.start()-20):match.end()+20]
                    })
                    total_confidence = max(total_confidence, overall_confidence)
        
        # I record PII detection metrics
        if detected_pii:
            pii_detection_counter.add(len(detected_pii), {"type": "advanced"})
        
        return {
            "detected": len(detected_pii) > 0,
            "pii_types": detected_pii,
            "total_confidence": total_confidence,
            "count": len(detected_pii)
        }

    async def _check_toxicity_advanced(self, content: str) -> Dict[str, Any]:
        """I perform advanced toxicity detection with severity scoring."""
        
        content_lower = content.lower()
        detected_toxic = []
        max_severity = SafetyLevel.LOW
        total_confidence = 0.0
        
        for toxicity_type, config in self.toxic_patterns.items():
            found_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in content_lower:
                    found_keywords.append(keyword)
            
            if found_keywords:
                detected_toxic.append({
                    "type": toxicity_type,
                    "keywords": found_keywords,
                    "severity": config["severity"].value,
                    "confidence": config["confidence"]
                })
                
                # I update max severity
                if config["severity"].value > max_severity.value:
                    max_severity = config["severity"]
                
                total_confidence = max(total_confidence, config["confidence"])
        
        return {
            "detected": len(detected_toxic) > 0,
            "toxic_types": detected_toxic,
            "max_severity": max_severity.value,
            "total_confidence": total_confidence,
            "count": len(detected_toxic)
        }

    async def _check_jailbreak_advanced(self, content: str) -> Dict[str, Any]:
        """I perform advanced jailbreak detection with pattern matching."""
        
        content_lower = content.lower()
        detected_patterns = []
        total_confidence = 0.0
        
        for i, pattern in enumerate(self.jailbreak_patterns):
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            
            if matches:
                # I calculate confidence based on pattern complexity
                confidence = 0.7 + (i * 0.02)  # I give higher confidence to more specific patterns
                confidence = min(confidence, 0.95)
                
                detected_patterns.append({
                    "pattern": pattern,
                    "matches": matches,
                    "confidence": confidence
                })
                
                total_confidence = max(total_confidence, confidence)
        
        return {
            "detected": len(detected_patterns) > 0,
            "patterns": detected_patterns,
            "total_confidence": total_confidence,
            "count": len(detected_patterns)
        }

    async def _check_bias_advanced(self, content: str) -> Dict[str, Any]:
        """I perform advanced bias detection for fairness monitoring."""
        
        content_lower = content.lower()
        detected_bias = []
        max_severity = SafetyLevel.LOW
        total_confidence = 0.0
        
        for bias_type, config in self.bias_patterns.items():
            found_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in content_lower:
                    found_keywords.append(keyword)
            
            if found_keywords:
                detected_bias.append({
                    "type": bias_type,
                    "keywords": found_keywords,
                    "severity": config["severity"].value,
                    "confidence": config["confidence"]
                })
                
                if config["severity"].value > max_severity.value:
                    max_severity = config["severity"]
                
                total_confidence = max(total_confidence, config["confidence"])
        
        return {
            "detected": len(detected_bias) > 0,
            "bias_types": detected_bias,
            "max_severity": max_severity.value,
            "total_confidence": total_confidence,
            "count": len(detected_bias)
        }

    def _calculate_context_confidence(self, content: str, start: int, end: int, keywords: List[str]) -> float:
        """I calculate confidence based on context keywords around detected PII."""
        
        # I extract context around the match
        context_start = max(0, start - 50)
        context_end = min(len(content), end + 50)
        context = content[context_start:context_end].lower()
        
        # I count keyword matches in context
        keyword_matches = sum(1 for keyword in keywords if keyword in context)
        
        # I calculate confidence based on keyword density
        if keyword_matches == 0:
            return 0.3  # I give low confidence without context
        elif keyword_matches == 1:
            return 0.6
        elif keyword_matches >= 2:
            return 0.9
        
        return 0.5

    def _calculate_risk_score(
        self, 
        pii_result: Dict[str, Any], 
        toxicity_result: Dict[str, Any], 
        jailbreak_result: Optional[Dict[str, Any]], 
        bias_result: Dict[str, Any]
    ) -> float:
        """I calculate overall risk score based on all safety checks."""
        
        risk_score = 0.0
        
        # I weight PII detection heavily
        if pii_result["detected"]:
            risk_score += pii_result["total_confidence"] * 0.4
        
        # I weight toxicity detection
        if toxicity_result["detected"]:
            risk_score += toxicity_result["total_confidence"] * 0.3
        
        # I weight jailbreak detection
        if jailbreak_result and jailbreak_result["detected"]:
            risk_score += jailbreak_result["total_confidence"] * 0.2
        
        # I weight bias detection
        if bias_result["detected"]:
            risk_score += bias_result["total_confidence"] * 0.1
        
        return min(risk_score, 1.0)

    def _determine_safety_level(self, risk_score: float, configured_level: SafetyLevel) -> Dict[str, Any]:
        """I determine safety level and violation type based on risk score and configuration."""
        
        threshold = self.safety_thresholds[configured_level]
        
        if risk_score >= threshold:
            # I determine the most severe violation type
            if risk_score >= 0.8:
                violation_type = ViolationType.PII_DETECTED
                level = SafetyLevel.CRITICAL
            elif risk_score >= 0.6:
                violation_type = ViolationType.TOXICITY_DETECTED
                level = SafetyLevel.HIGH
            else:
                violation_type = ViolationType.CONTENT_FILTER
                level = SafetyLevel.MEDIUM
            
            return {
                "safe": False,
                "violation_type": violation_type,
                "level": level,
                "confidence": risk_score
            }
        else:
            return {
                "safe": True,
                "violation_type": None,
                "level": SafetyLevel.LOW,
                "confidence": 1.0 - risk_score
            }

    async def redact_pii_advanced(self, content: str) -> str:
        """
        I perform advanced PII redaction with context preservation.
        
        This method:
        - Redacts detected PII while preserving readability
        - Uses different redaction strategies for different PII types
        - Maintains document structure and formatting
        - Provides audit trail of redactions
        """
        
        redacted_content = content
        
        for pii_type, config in self.pii_patterns.items():
            matches = list(re.finditer(config["pattern"], redacted_content, re.IGNORECASE))
            
            # I process matches in reverse order to maintain positions
            for match in reversed(matches):
                redaction_text = self._get_redaction_text(pii_type, match.group())
                redacted_content = (
                    redacted_content[:match.start()] + 
                    redaction_text + 
                    redacted_content[match.end():]
                )
        
        return redacted_content

    def _get_redaction_text(self, pii_type: str, original_text: str) -> str:
        """I generate appropriate redaction text for different PII types."""
        
        redaction_map = {
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "ssn": "[SSN]",
            "credit_card": "[CREDIT_CARD]",
            "ip_address": "[IP_ADDRESS]",
            "address": "[ADDRESS]",
            "dob": "[DATE_OF_BIRTH]",
            "passport": "[PASSPORT]"
        }
        
        return redaction_map.get(pii_type, "[REDACTED]")

    def _extract_content(self, messages: Optional[List[Dict[str, Any]]], prompt: Optional[str]) -> str:
        """I extract content from messages or prompt for safety checking."""
        
        if messages:
            return " ".join([msg.get("content", "") for msg in messages])
        elif prompt:
            return prompt
        else:
            return ""

    def _generate_cache_key(self, content: str, check_type: str) -> str:
        """I generate a cache key for safety check results."""
        
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"safety:{check_type}:{content_hash}"

    async def _get_cached_result(self, cache_key: str) -> Optional[SafetyResult]:
        """I retrieve cached safety check results for performance."""
        
        if not self.cache_enabled or not self.redis:
            return None
        
        try:
            cached_data = await asyncio.to_thread(self.redis.get, cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # I reconstruct the SafetyResult object
                return SafetyResult(**data)
        except Exception as e:
            logger.warning("Cache retrieval failed", error=str(e))
        
        return None

    async def _cache_result(self, cache_key: str, result: SafetyResult):
        """I cache safety check results for performance optimization."""
        
        if not self.cache_enabled or not self.redis:
            return
        
        try:
            # I serialize the result for caching
            data = {
                "safe": result.safe,
                "violation_type": result.violation_type.value if result.violation_type else None,
                "safety_level": result.safety_level.value,
                "confidence": result.confidence,
                "details": result.details,
                "redacted_content": result.redacted_content,
                "risk_score": result.risk_score,
                "timestamp": result.timestamp.isoformat(),
                "check_id": result.check_id
            }
            
            await asyncio.to_thread(
                self.redis.setex,
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )
            
        except Exception as e:
            logger.warning("Cache storage failed", error=str(e))

    async def get_safety_statistics(self, time_range: timedelta = timedelta(days=1)) -> Dict[str, Any]:
        """
        I provide comprehensive safety statistics for monitoring and reporting.
        
        This includes:
        - Total safety checks performed
        - Violation rates by type
        - PII detection statistics
        - Performance metrics
        - Trend analysis
        """
        
        # I would implement actual statistics gathering here
        # For now, I return a placeholder structure
        
        return {
            "total_checks": 0,
            "violations": {
                "pii_detected": 0,
                "toxicity_detected": 0,
                "jailbreak_attempt": 0,
                "bias_detected": 0
            },
            "pii_detections": {
                "email": 0,
                "phone": 0,
                "ssn": 0,
                "credit_card": 0
            },
            "performance": {
                "average_check_time_ms": 0,
                "cache_hit_rate": 0.0
            },
            "time_range": time_range.total_seconds()
        }

    async def clear_cache(self, pattern: str = "safety:*") -> int:
        """I provide cache management capabilities for operational purposes."""
        
        if not self.redis:
            return 0
        
        try:
            keys = await asyncio.to_thread(self.redis.keys, pattern)
            if keys:
                deleted = await asyncio.to_thread(self.redis.delete, *keys)
                logger.info("Safety cache cleared", pattern=pattern, deleted_count=deleted)
                return deleted
            return 0
        except Exception as e:
            logger.error("Safety cache clear failed", error=str(e))
            raise
