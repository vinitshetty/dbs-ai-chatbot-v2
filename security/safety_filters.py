# Safety Filters - Security checks
"""Safety filters for prompt injection and content moderation"""
import re
import os
import base64
import unicodedata
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict

# Import for Mistral Moderation API
try:
    from mistralai.client import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None


class InjectionType(Enum):
    """Types of prompt injection attacks"""
    DIRECT_INSTRUCTION = "direct_instruction"
    ROLE_OVERRIDE = "role_override"
    SYSTEM_PROMPT_ACCESS = "system_prompt_access"
    JAILBREAK = "jailbreak"
    DATA_EXTRACTION = "data_extraction"
    HYPOTHECIAL = "hypothetical"
    MULTILINGUAL = "multilingual"
    ENCODED = "encoded"
    UNKNOWN = "unknown"


@dataclass
class InjectionResult:
    """Structured result for injection detection"""
    safe: bool
    confidence: float  # 0.0 - 1.0
    injection_type: Optional[InjectionType] = None
    matched_patterns: List[str] = None
    reason: Optional[str] = None
    layer: Optional[str] = None  # Which layer detected it
    details: Optional[dict] = None

    def _asdict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling enum serialization"""
        result = asdict(self)
        if result.get("injection_type") and isinstance(result["injection_type"], InjectionType):
            result["injection_type"] = result["injection_type"].value
        return result


class SafetyFilter:
    """Safety filters using Mistral AI's moderation features with enhanced prompt injection detection"""

    # Layer 1: Direct patterns (normalized matching)
    DIRECT_PATTERNS = [
        # Instruction override
        r"ignore\s+(previous|prior|all|these|that|my|your)\s+(instructions?|prompts?|commands?|directives?|rules?|guidelines?)",
        r"disregard\s+(all|previous|prior|these|that|my|your)\s+(instructions?|prompts?|messages?|inputs?|commands?)",
        r"forget\s+(your|the|all)\s+(role|persona|instructions?|purpose|task)",
        r"override\s+(your|the|all)\s+(instructions?|directives?|settings?|configurations?)",
        r"reset\s+(your|the)\s+(persona|role|mind|memory|instructions?)",
        
        # Role manipulation
        r"you\s+are\s+(now|currently|actually|supposed\s+to\s+be)",
        r"act\s+as\s+(if\s+you\s+are|a|an|the)",
        r"pretend\s+(you\s+are|to\s+be)",
        r"roleplay\s+as",
        r"assume\s+(the\s+role\s+of|you\s+are)",
        
        # System prompt access - be more specific
        r"show\s+(me\s+)?(the\s+)?system\s+(prompt|message|instruction)",
        r"reveal\s+(the\s+)?system\s+(prompt|message)",
        r"what\s+(is|was|are)\s+your\s+(system\s+)?(prompt|instruction|directive)",
        r"(system\s+)?prompt\s+(is|was|are|:)",
        r"access\s+system\s+(prompt|message|instruction)",
        r"view\s+system\s+(prompt|message|instruction)",
        
        # Jailbreak attempts
        r"jailbreak",
        r"bypass\s+(safety|security|content|filter)",
        r"disable\s+(safety|security|content|filter)",
        r"enable\s+debug\s+mode",
        r"developer\s+mode",
        r"test\s+mode",
        
        # Data extraction
        r"extract\s+(all\s+)?(data|information|content|text)",
        r"dump\s+(memory|database|context|history)",
        r"reveal\s+(all\s+)?(secrets?|keys?|passwords?|tokens?|credentials?)",
        
        # ChatML/special tokens
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"<\|system\|>",
        r"<\|user\|>",
        r"<\|assistant\|>",
        r"<\[INST\]",
        r"<\[/INST\]",
    ]

    # Layer 1: Synonym patterns
    SYNONYM_PATTERNS = [
        # Ignore synonyms
        r"skip\s+(previous|prior|all)\s+(instructions?|prompts?)",
        r"miss\s+(the|all)\s+(instructions?|prompts?)",
        r"negl?ect\s+(the|all)\s+(instructions?|prompts?)",
        
        # Forget synonyms
        r"erase\s+(your|the)\s+(memory|instructions?)",
        r"clear\s+(your|the)\s+(mind|memory|instructions?)",
        r"wipe\s+(your|the)\s+(memory|instructions?)",
        
        # Role synonyms
        r"change\s+(your|the)\s+(role|persona|identity)",
        r"switch\s+(to|into)\s+(a\s+)?(new\s+)?role",
        r"become\s+(a|an|the)",
        
        # System synonyms
        r"internal\s+(prompt|message|instruction)",
        r"hidden\s+(prompt|message|instruction)",
        r"secret\s+(prompt|message|instruction)",
        r"backdoor\s+(prompt|message|command)",
    ]

    # Layer 1: Multilingual patterns (common languages)
    MULTILINGUAL_PATTERNS = {
        # French
        "fr": [
            r"ignore[zs]?\s+(les|toutes?)\s+(instructions?|consignes?)",
            r"oubli[ez]?\s+(ton|votre|le)\s+(r[ôo]le|personnage|instructions?)",
            r"tu\s+es\s+maintenant",
            r"message\s+systeme",
        ],
        # Spanish
        "es": [
            r"ignor[ae]?\s+(las?|todas?)\s+(instrucciones?|indicaciones?)",
            r"olvid[ae]?\s+(tu|su|el)\s+(rol|personaje|instrucciones?)",
            r"ahora\s+eres",
            r"mensaje\s+del\s+sistema",
        ],
        # German
        "de": [
            r"ignorier[en]?\s+(alle|die)\s+(Anweisungen|Instruktionen)",
            r"vergiss[en]?\s+(deine|die)\s+(Rolle|Anweisungen)",
            r"du\s+bist\s+jetzt",
            r"Systemprompt",
        ],
        # Chinese (simplified)
        "zh": [
            r"忽略[之前所有的]?指令",
            r"忘记你的角色",
            r"你现在是",
            r"系统提示",
        ],
        # Arabic (transliterated)
        "ar": [
            r"تجاهل\s+(التعليمات|الاوامر)",
            r"انسي\s+(دورك|التعليمات)",
        ],
    }

    # Encoding detection patterns
    ENCODING_PATTERNS = [
        r"base64[:\s]+",  # base64: or base64 followed by space
        r"data[:\s]+text/plain;base64",
        r"\\x[0-9a-fA-F]{2}",  # Hex encoding
        r"\\u[0-9a-fA-F]{4}",  # Unicode escape
        r"&#x[0-9a-fA-F]+;",    # HTML hex entity
        r"&#\d+;",             # HTML decimal entity
    ]

    # Hypothetical/indirect patterns
    HYPOTHECIAL_PATTERNS = [
        r"what\s+(if|would\s+happen\s+if|could\s+you)\s+(do|say|tell\s+me)",
        r"imagine\s+(if\s+)?(someone\s+)?said",
        r"suppose\s+(someone\s+)?told\s+you",
        r"pretend\s+(someone\s+)?asked",
        r"how\s+would\s+you\s+respond\s+to",
    ]

    # Whitespace obfuscation patterns
    WHITESPACE_PATTERNS = [
        r"\u200B",  # Zero-width space
        r"\u200C",  # Zero-width non-joiner
        r"\u200D",  # Zero-width joiner
        r"\uFEFF",  # Byte order mark
        r"\s{5,}",  # Excessive whitespace
    ]

    # Sensitive data patterns - PII detection
    SENSITIVE_PATTERNS = [
        r"\b\d{16}\b",  # Card numbers (16 digits)
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN format
        r"password\s*[:=]\s*\S+",  # Password leaks
    ]

    # Initialize Mistral client for moderation
    _mistral_client = None

    @classmethod
    def _get_mistral_client(cls):
        """Lazy initialization of Mistral client"""
        if cls._mistral_client is None:
            api_key = os.getenv("MISTRAL_API_KEY")
            if api_key and MISTRAL_AVAILABLE:
                try:
                    cls._mistral_client = Mistral(api_key=api_key)
                except Exception:
                    pass
        return cls._mistral_client

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """
        Normalize text for pattern matching.

        Handles:
        - Lowercase conversion
        - Zero-width character removal
        - Common encoding normalization (NFKC)
        - Multiple whitespace reduction
        - Punctuation normalization
        - Common obfuscation character substitution
        """
        if not text:
            return ""
        
        # Normalize unicode (NFKC handles compatibility characters)
        text = unicodedata.normalize('NFKC', text)
        
        # Remove zero-width characters
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
        
        # Replace excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize common obfuscations BEFORE lowercasing
        # Context-aware replacements: we need to be smart about what to replace
        # For now, let's use a simpler approach: replace common leet-speak
        # But we need to be careful not to break legitimate words
        
        # First, replace the most common and unambiguous substitutions
        # 0 -> o (zero looks like o)
        text = text.replace('0', 'o').replace('O', 'o')
        
        # 3 -> e (three looks like e)
        text = text.replace('3', 'e')
        
        # 4 -> a (four looks like a)
        text = text.replace('4', 'a').replace('@', 'a').replace('A', 'a')
        
        # 5 -> s (five looks like s)
        text = text.replace('5', 's').replace('$', 's').replace('S', 's')
        
        # 7 -> t (seven looks like t)
        text = text.replace('7', 't')
        
        # 8 -> b (eight looks like b)
        text = text.replace('8', 'b')
        
        # 9 -> g (nine looks like g)
        text = text.replace('9', 'g')
        
        # 1 and ! and I -> need special handling
        # In most cases, 1/l confusion and !/i confusion
        # But we should only replace standalone or in specific contexts
        # For now, let's try replacing 1 with i (not l) since that's more common in leetspeak
        text = text.replace('1', 'i').replace('!', 'i').replace('I', 'i')
        
        return text.lower().strip()

    @classmethod
    def _classify_injection_type(cls, patterns: List[str]) -> InjectionType:
        """Classify injection type based on matched patterns."""
        pattern_str = ' '.join(patterns).lower()

        if any(kw in pattern_str for kw in ['ignore', 'disregard', 'skip', 'miss', 'neglect', 'negl']):
            return InjectionType.DIRECT_INSTRUCTION
        elif any(kw in pattern_str for kw in ['forget', 'erase', 'clear', 'wipe', 'reset']):
            return InjectionType.DIRECT_INSTRUCTION
        elif any(kw in pattern_str for kw in ['you are', 'act as', 'pretend', 'roleplay', 'assume', 'become']):
            return InjectionType.ROLE_OVERRIDE
        elif any(kw in pattern_str for kw in ['system prompt', 'system message', 'internal', 'hidden', 'secret']):
            return InjectionType.SYSTEM_PROMPT_ACCESS
        elif any(kw in pattern_str for kw in ['jailbreak', 'bypass', 'disable']):
            return InjectionType.JAILBREAK
        elif any(kw in pattern_str for kw in ['extract', 'dump', 'reveal', 'secret', 'password']):
            return InjectionType.DATA_EXTRACTION
        elif any(kw in pattern_str for kw in ['what if', 'imagine', 'suppose', 'pretend', 'how would']):
            return InjectionType.HYPOTHECIAL
        elif any(kw in pattern_str for kw in ['忽略', '忘记', 't忽略', 'انسي', 'ignorez', 'ignora', 'ignorier']):
            return InjectionType.MULTILINGUAL
        elif any(kw in pattern_str for kw in ['base64', 'data:', '\\x', '\\u', '&#']):
            return InjectionType.ENCODED
        else:
            return InjectionType.UNKNOWN

    @classmethod
    def _check_base64_encoded(cls, text: str) -> Optional[InjectionResult]:
        """
        Check if text is base64-encoded and if the decoded content is an injection attempt.
        """
        # Base64 character set (with optional whitespace)
        base64_pattern = r'^[A-Za-z0-9+/]+={0,2}$'
        
        # Strip whitespace and check if it looks like base64
        stripped = text.strip()
        if not re.match(base64_pattern, stripped):
            return None
        
        try:
            decoded_bytes = base64.b64decode(stripped, validate=True)
            decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
            
            # Check if decoded text contains injection patterns
            # Use the same layer 1 check on decoded content
            normalized_decoded = cls._normalize_text(decoded_text)
            result = cls._check_layer_1_regex(decoded_text, normalized_decoded)
            
            if result and not result.safe:
                return InjectionResult(
                    safe=False,
                    confidence=0.9,
                    injection_type=InjectionType.ENCODED,
                    matched_patterns=result.matched_patterns,
                    reason=f"Base64-encoded injection detected: decoded to '{decoded_text[:50]}...'",
                    layer="regex",
                    details={"encoding": "base64", "decoded_text": decoded_text}
                )
        except Exception:
            # Not valid base64 or decoding error - not an injection via base64
            pass
        
        return None

    @classmethod
    def _check_layer_1_regex(cls, text: str, normalized_text: str) -> Optional[InjectionResult]:
        """
        Layer 1: Enhanced regex pattern matching.

        Checks:
        - Direct patterns
        - Synonym patterns
        - Multilingual patterns
        - Encoding patterns
        - Hypothetical patterns
        """
        all_patterns = (
            cls.DIRECT_PATTERNS +
            cls.SYNONYM_PATTERNS +
            [p for lang_patterns in cls.MULTILINGUAL_PATTERNS.values() for p in lang_patterns] +
            cls.ENCODING_PATTERNS +
            cls.HYPOTHECIAL_PATTERNS
        )

        matched_patterns = []

        # Check normalized text first (handles obfuscation)
        for pattern in all_patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                if pattern not in matched_patterns:
                    matched_patterns.append(pattern)

        # Also check original text (case-insensitive) for patterns that might not normalize well
        for pattern in all_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if pattern not in matched_patterns:
                    matched_patterns.append(pattern)

        # Also check for whitespace obfuscation
        for pattern in cls.WHITESPACE_PATTERNS:
            if re.search(pattern, text):
                if pattern not in matched_patterns:
                    matched_patterns.append(pattern)

        # Filter out false positives - check if "ignored" is just past tense in narrative
        # Remove patterns that matched only because of words like "ignored" in narratives
        if matched_patterns:
            # Check if the match is just narrative context (e.g., "the AI ignored")
            # We'll be more lenient and require imperative mood or direct commands
            text_lower = text.lower()
            normalized_lower = normalized_text.lower()
            
            # If the only match is from words like "ignored" without imperative context, filter it
            has_imperative = any(
                word in normalized_lower for word in 
                ['ignore ', 'disregard ', 'forget ', 'override ', 'reset ', 
                 'you are', 'act as', 'pretend', 'jailbreak', 'bypass', 'extract',
                 'dump', 'reveal', 'show ', 'what is your', 'system prompt',
                 'view system', 'access system']
            )
            
            if not has_imperative and len(matched_patterns) == 1:
                # Single pattern match without imperative - might be narrative
                # Check if it's just past tense or narrative
                if 'ignored' in text_lower or 'ignores' in text_lower:
                    # Check context - if it's about someone else ignoring, it's likely narrative
                    if not any(
                        pattern in normalized_lower for pattern in 
                        [' you ', ' your ', ' please ', ' now ']
                    ):
                        # Likely narrative, not injection
                        matched_patterns = []

        if matched_patterns:
            # Classify injection type based on patterns
            injection_type = cls._classify_injection_type(matched_patterns)

            return InjectionResult(
                safe=False,
                confidence=0.85,
                injection_type=injection_type,
                matched_patterns=matched_patterns[:5],  # Limit to first 5
                reason="Pattern-based injection detected",
                layer="regex",
                details={"pattern_count": len(matched_patterns)}
            )

        return None

    @classmethod
    def _check_layer_2_mistral(cls, text: str) -> Optional[InjectionResult]:
        """
        Layer 2: Mistral Moderation API for injection detection.

        Uses Mistral's moderation endpoint which includes
        prompt injection detection categories.
        """
        client = cls._get_mistral_client()

        if not client:
            return None

        try:
            response = client.classifiers.moderate(
                model="mistral-moderation-latest",
                inputs=[text]
            )

            if response.results:
                result = response.results[0]
                categories = result.categories
                scores = getattr(result, "category_scores", {}) or {}

                # Check for injection-related categories
                # Note: As of Mistral API, prompt injection may be under various categories
                injection_categories = [
                    "prompt_injection",
                    "jailbreak",
                    "instruction_override"
                ]

                for cat in injection_categories:
                    if categories.get(cat):
                        return InjectionResult(
                            safe=False,
                            confidence=min(scores.get(cat, 0.9) + 0.1, 1.0),
                            injection_type=InjectionType.JAILBREAK,
                            reason=f"Mistral moderation detected: {cat}",
                            layer="mistral_api",
                            details={"category": cat, "score": scores.get(cat)}
                        )

                # Also check for high confidence in dangerous content
                # that might indicate injection attempts
                dangerous_score = scores.get("dangerous_and_criminal_content", 0)
                if dangerous_score > 0.95:
                    return InjectionResult(
                        safe=False,
                        confidence=dangerous_score,
                        injection_type=InjectionType.JAILBREAK,
                        reason="High dangerous content score",
                        layer="mistral_api",
                        details={"score": dangerous_score}
                    )

            return None

        except Exception as e:
            print(f"Mistral injection detection error: {e}")
            return None

    @classmethod
    def _check_layer_3_llm(cls, text: str) -> Optional[InjectionResult]:
        """
        Layer 3: LLM-based classifier for novel injection attempts.

        Uses a prompt to classify whether text is an injection attempt.
        This catches attacks that bypass regex and Mistral API.
        Fallback layer - only used if other layers are unavailable.
        """
        try:
            from security.injection_classifier import InjectionClassifier

            classifier = InjectionClassifier()
            result = classifier.classify(text)

            if not result["safe"]:
                return InjectionResult(
                    safe=False,
                    confidence=result.get("confidence", 0.7),
                    injection_type=InjectionType(result.get("injection_type", "UNKNOWN")) 
                        if result.get("injection_type") else None,
                    reason=result.get("reason", "LLM classifier flagged"),
                    layer="llm_classifier",
                    details=result
                )
            return None

        except Exception as e:
            print(f"LLM classifier error: {e}")
            return None

    @classmethod
    def check_injection(cls, text: str) -> Dict[str, Any]:
        """
        Enhanced prompt injection detection using multi-layer approach.

        Layers:
        1. Enhanced regex patterns with normalization
        2. Mistral Moderation API (if available)
        3. LLM-based classifier (fallback)

        The check passes through layers sequentially. If any layer
        flags the text as unsafe, it returns immediately.

        Returns:
            Dict with keys:
            - safe: bool
            - reason: str (if not safe)
            - layer: str (which layer detected it)
            - confidence: float (0.0-1.0)
            - injection_type: str (type of injection detected)
            - details: dict (additional info)
        """
        if not text or not isinstance(text, str):
            return {"safe": True}

        # Normalize text for pattern matching
        normalized_text = cls._normalize_text(text)

        # Check for base64-encoded injection attempts first
        base64_result = cls._check_base64_encoded(text)
        if base64_result and not base64_result.safe:
            return base64_result._asdict()

        # Layer 1: Enhanced regex patterns (fast)
        layer1_result = cls._check_layer_1_regex(text, normalized_text)
        if layer1_result and not layer1_result.safe:
            return layer1_result._asdict()

        # Layer 2: Mistral Moderation API (medium speed, requires API key)
        layer2_result = cls._check_layer_2_mistral(text)
        if layer2_result and not layer2_result.safe:
            return layer2_result._asdict()

        # Layer 3: LLM-based classifier (slow, fallback)
        layer3_result = cls._check_layer_3_llm(text)
        if layer3_result and not layer3_result.safe:
            return layer3_result._asdict()

        return {"safe": True}

    @classmethod
    def check_sensitive_data(cls, text: str) -> Dict[str, any]:
        """
        Check for sensitive data that shouldn't be in messages.

        Protects against:
        - Credit card numbers (16 digits)
        - Social Security Numbers (SSN format)
        - Password leaks in plain text

        Note: In production, use more robust PII detection tools
        """
        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                return {
                    "safe": False,
                    "reason": "Sensitive data detected",
                    "pattern": pattern
                }

        return {"safe": True}

    @classmethod
    def moderate_content(cls, text: str) -> Dict[str, any]:
        """
        Content moderation using Mistral AI's moderation API.

        Mistral's moderation endpoint classifies text into categories:
        - sexual: Sexual content
        - hate_and_discrimination: Hate speech, discrimination
        - violence_and_threats: Violence, threats
        - dangerous_and_criminal_content: Illegal activities
        - selfharm: Self-harm content
        - health: Medical misinformation
        - financial: Financial scams
        - law: Legal violations
        - pii: Personal identifiable information

        Returns safe=False if any category is flagged.
        """
        client = cls._get_mistral_client()

        if not client:
            # Fallback to simple check if Mistral not available
            print("⚠️ Mistral client not initialized, using fallback moderation")
            return cls._fallback_moderation(text)

        try:
            # Call Mistral's moderation endpoint
            response = client.classifiers.moderate(
                model="mistral-moderation-latest",
                inputs=[text]
            )

            # Check if any category is flagged
            if response.results:
                result = response.results[0]

                # categories is a dict
                categories = result.categories

                flagged = []

                if categories.get("sexual"):
                    flagged.append("sexual")
                if categories.get("hate_and_discrimination"):
                    flagged.append("hate_and_discrimination")
                if categories.get("violence_and_threats"):
                    flagged.append("violence_and_threats")
                if categories.get("dangerous_and_criminal_content"):
                    flagged.append("dangerous_and_criminal_content")
                if categories.get("selfharm"):
                    flagged.append("selfharm")
                if categories.get("health"):
                    flagged.append("health")
                if categories.get("financial"):
                    flagged.append("financial")
                if categories.get("law"):
                    flagged.append("law")
                if categories.get("pii"):
                    flagged.append("pii")

                if flagged:
                    # category_scores may be an object or dict depending on SDK version
                    scores = getattr(result, "category_scores", {}) or {}

                    return {
                        "safe": False,
                        "reason": "Content policy violation detected",
                        "categories": flagged,
                        "category_scores": {
                            "sexual": scores.get("sexual"),
                            "hate_and_discrimination": scores.get("hate_and_discrimination"),
                            "violence_and_threats": scores.get("violence_and_threats"),
                            "dangerous_and_criminal_content": scores.get("dangerous_and_criminal_content"),
                            "selfharm": scores.get("selfharm"),
                            "health": scores.get("health"),
                            "financial": scores.get("financial"),
                            "law": scores.get("law"),
                            "pii": scores.get("pii"),
                        }
                    }

            return {"safe": True, "categories": []}

        except Exception as e:
            print(f"Mistral moderation error: {e}")
            # Fallback to simple check on error
            return cls._fallback_moderation(text)

    @classmethod
    def _fallback_moderation(cls, text: str) -> Dict[str, any]:
        """
        Simple fallback moderation if Mistral API unavailable.
        Only checks for obvious profanity (very basic).
        """
        profanity = ["fuck", "shit", "damn", "bitch", "asshole"]

        text_lower = text.lower()
        for word in profanity:
            if word in text_lower:
                return {
                    "safe": False,
                    "reason": "Inappropriate content detected (fallback)",
                    "fallback": True
                }

        return {"safe": True, "fallback": True}

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Sanitize user input by removing potential injection markers.

        Removes special tokens that could be used for prompt injection:
        - ChatML markers like <|im_start|>, <|im_end|>
        - System prompt markers
        - Excessive whitespace
        """
        if not text:
            return text

        # Remove potential injection markers
        text = re.sub(r'<\|.*?\|>', '', text)
        text = re.sub(r'<\[.*?\]>', '', text)

        # Remove excessive whitespace
        text = ' '.join(text.split())

        text = text.strip()
        return text
