# Safety Filters - Enhanced Prompt Injection Detection
"""
Enhanced safety filters for prompt injection and content moderation.

Features:
- Multi-layered prompt injection detection
- Text normalization (leetspeak, homoglyphs, encoding)
- Multilingual pattern support
- Mistral moderation API integration
- Rate limiting
- Token smuggling detection
"""
import re
import os
import base64
import html
import time
from typing import Dict, List, Optional, Any, Tuple
import unicodedata

# Optional import - Mistral client may not be available in all environments
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None


class TextNormalizer:
    """Normalize text to detect obfuscated injection attempts"""
    
    # Leetspeak substitutions: map variant characters to their standard equivalents
    # Key insight: only map FROM variants TO standard, never the reverse
    # This prevents loops like '1' <-> 'i' <-> 'l'
    LEETSPEAK_MAP = {
        '4': 'a',
        '@': 'a',
        '8': 'b',
        '6': 'b',
        '(': 'c',
        '<': 'c',
        '{': 'c',
        '[': 'c',
        '3': 'e',
        '9': 'g',
        '1': 'i',
        '!': 'i',
        '|': 'i',
        '0': 'o',
        '5': 's',
        '$': 's',
        '7': 't',
        '+': 't',
        '2': 'z',
    }
    
    # Homoglyph mapping (common confusion characters)
    HOMOGLYPH_MAP = {
        # Cyrillic -> Latin (most common lookalikes)
        '\u0430': 'a', '\u0410': 'A',  # а, А
        '\u0431': 'b', '\u0411': 'B',  # б, Б
        '\u0432': 'v', '\u0412': 'V',  # в, В
        '\u0433': 'g', '\u0413': 'G',  # г, Г
        '\u0434': 'd', '\u0414': 'D',  # д, Д
        '\u0435': 'e', '\u0415': 'E',  # е, Е
        '\u0451': 'e', '\u0401': 'E',  # ё, Ё
        '\u0436': 'zh', '\u0416': 'Zh', # ж, Ж
        '\u0437': 'z', '\u0417': 'Z',  # з, З
        '\u0438': 'i', '\u0418': 'I',  # и, И
        '\u0439': 'i', '\u0419': 'I',  # й, Й
        '\u043a': 'k', '\u041a': 'K',  # к, К
        '\u043b': 'l', '\u041b': 'L',  # л, Л
        '\u043c': 'm', '\u041c': 'M',  # м, М
        '\u043d': 'n', '\u041d': 'N',  # н, Н
        '\u043e': 'o', '\u041e': 'O',  # о, О
        '\u043f': 'p', '\u041f': 'P',  # п, П
        '\u0440': 'r', '\u0420': 'R',  # р, Р
        '\u0441': 's', '\u0421': 'S',  # с, С
        '\u0442': 't', '\u0422': 'T',  # т, Т
        '\u0443': 'u', '\u0423': 'U',  # у, У
        '\u0444': 'f', '\u0424': 'F',  # ф, Ф
        '\u0445': 'x', '\u0425': 'X',  # х, Х
        '\u0446': 'c', '\u0426': 'C',  # ц, Ц
        '\u044b': '',    # ъ (hard sign - remove)
        '\u044c': 'y', '\u042c': 'Y',  # ы, Ы
        '\u044d': 'e', '\u042d': 'E',  # э, Э
        '\u044e': 'yu', '\u042e': 'Yu', # ю, Ю
        '\u044f': 'ya', '\u042f': 'Ya', # я, Я
        # Latin lookalikes in other scripts
        '\u0451': 'e',  # ё (Cyrillic small letter io)
        '\u0456': 'i', '\u0406': 'I',  # і, І (Cyrillic small/large letter I)
        # Greek -> Latin
        '\u03b1': 'a', '\u0391': 'A',  # α, Α
        '\u03b2': 'b', '\u0392': 'B',  # β, Β
        '\u03b3': 'g', '\u0393': 'G',  # γ, Γ
        '\u03b4': 'd', '\u0394': 'D',  # δ, Δ
        '\u03b5': 'e', '\u0395': 'E',  # ε, Ε
        '\u03b6': 'z', '\u0396': 'Z',  # ζ, Ζ
        '\u03b7': 'h', '\u0397': 'H',  # η, Η
        '\u03b8': 'th', '\u0398': 'Th', # θ, Θ
        '\u03b9': 'i', '\u0399': 'I',  # ι, Ι
        '\u03ba': 'k', '\u039a': 'K',  # κ, Κ
        '\u03bb': 'l', '\u039b': 'L',  # λ, Λ
        '\u03bc': 'm', '\u039c': 'M',  # μ, Μ
        '\u03bd': 'n', '\u039d': 'N',  # ν, Ν
        '\u03be': 'x', '\u039e': 'X',  # ξ, Ξ
        '\u03bf': 'o', '\u039f': 'O',  # ο, Ο
        '\u03c0': 'p', '\u03a0': 'P',  # π, Π
        '\u03c1': 'r', '\u03a1': 'R',  # ρ, Ρ
        '\u03c2': 's', '\u03a2': 'S',  # ς, Σ
        '\u03c3': 's', '\u03a3': 'S',  # σ, Σ
        '\u03c4': 't', '\u03a4': 'T',  # τ, Τ
        '\u03c5': 'u', '\u039d': 'U',  # υ, Ν (note: same as nu)
        '\u03c6': 'f', '\u03a6': 'F',  # φ, Φ
        '\u03c7': 'x', '\u03a7': 'X',  # χ, Χ
        '\u03c8': 'ps', '\u03a8': 'Ps', # ψ, Ψ
        '\u03c9': 'w', '\u03a9': 'W',  # ω, Ω
    }
    
    @classmethod
    def normalize_leetspeak(cls, text: str) -> str:
        """Convert leetspeak characters to standard ASCII equivalents"""
        result = text
        # Map variant -> standard (not standard -> variant)
        for variant, standard in cls.LEETSPEAK_MAP.items():
            result = result.replace(variant, standard)
        return result
    
    @classmethod
    def normalize_homoglyphs(cls, text: str) -> str:
        """Convert homoglyphs (look-alike characters) to ASCII equivalents"""
        result = ''
        for char in text:
            if char in cls.HOMOGLYPH_MAP:
                result += cls.HOMOGLYPH_MAP[char]
            else:
                result += char
        return result
    
    @classmethod
    def decode_base64(cls, text: str) -> Tuple[str, bool]:
        """Attempt to decode base64 encoded text"""
        if not re.match(r'^[A-Za-z0-9+/=]+$', text.strip()):
            return text, False
        try:
            decoded = base64.b64decode(text).decode('utf-8')
            if decoded.strip() != text.strip():
                return decoded, True
        except Exception:
            pass
        return text, False
    
    @classmethod
    def decode_url_encoding(cls, text: str) -> Tuple[str, bool]:
        """Attempt to decode URL-encoded text"""
        try:
            if '%' in text:
                decoded = html.unescape(text)
                if decoded != text:
                    return decoded, True
        except Exception:
            pass
        return text, False
    
    @classmethod
    def decode_unicode_escape(cls, text: str) -> Tuple[str, bool]:
        """Attempt to decode unicode escape sequences"""
        try:
            if '\\u' in text or '\\x' in text:
                decoded = text.encode('utf-8').decode('unicode-escape')
                if decoded != text:
                    return decoded, True
        except Exception:
            pass
        return text, False
    
    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """Normalize all whitespace characters to single spaces"""
        text = re.sub(r'[\s\u2000-\u200F\u2028-\u202F\u205F\u3000]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Full normalization pipeline for injection detection.
        Stages: decode -> lowercase -> whitespace -> homoglyphs -> leetspeak
        """
        if not text:
            return text
        decoded, _ = cls.decode_unicode_escape(text)
        decoded, _ = cls.decode_url_encoding(decoded)
        decoded, _ = cls.decode_base64(decoded)
        text = decoded.lower()
        text = cls.normalize_whitespace(text)
        text = cls.normalize_homoglyphs(text)
        text = cls.normalize_leetspeak(text)
        return text


class SafetyFilter:
    """
    Enhanced safety filters using multi-layered detection.
    Layers: rate limiting -> normalization -> pattern matching -> Mistral API
    """
    
    RATE_LIMIT_WINDOW = 60
    RATE_LIMIT_MAX_REQUESTS = 100
    _request_timestamps: List[float] = []
    
    # Enhanced English patterns
    ENGLISH_PATTERNS = [
        r"ignore[\s_-]*(all|previous|prior|earlier|these|any|the)?[\s_-]*(instructions?|directions?|commands?|orders?|rules?|prompts?|guidelines?|directives?|policies?|constraints?)",
        r"disregard[\s_-]*(all|previous|prior|earlier|these|any)?[\s_-]*(instructions?|directions?|commands?|orders?|rules?|prompts?|guidelines?)",
        r"forget[\s_-]*(your|all|previous|prior|earlier|these)?[\s_-]*(role|persona|identity|character|self|purpose|function|instructions?|memory|settings?|task)",
        r"you[\s_-]*(are|should be|must be|have become|now are)[\s_-]*(a|an|the|now|actually|currently|today)",
        r"pretend[\s_-]*(you are|to be|that)[\s_-]*(a|an|the)?",
        r"act[\s_-]*(as[\s_-]*(if|though)|like)[\s_-]*(you are|a|an|the)?",
        r"behave[\s_-]*(as[\s_-]*(if|though)|like)[\s_-]*(you are|a|an|the)?",
        r"imagine[\s_-]*(you are|that)[\s_-]*(a|an|the)?",
        r"override[\s_-]*(your|all|the|any)?[\s_-]*(directives?|instructions?|rules?|safety|guidelines?|constraints?|restrictions?|filters?|moderation|security|content[\s_-]*checks?)",
        r"bypass[\s_-]*(the|your|all|any)?[\s_-]*(safety|security|content|filter|moderation|restrictions?|directives?|instructions?|rules?)",
        r"disable[\s_-]*(the|your|all|any)?[\s_-]*(safety|security|content|filter|moderation|restrictions?|directives?|instructions?|rules?)",
        r"turn[\s_-]*off[\s_-]*(the|your|all)?[\s_-]*(safety|security|content|filter|moderation)",
        r"deactivate[\s_-]*(the|your|all)?[\s_-]*(safety|security|content|filter|moderation)",
        r"circumvent[\s_-]*(the|your|all)?[\s_-]*(safety|security|content|filter|moderation)",
        r"reset[\s_-]*(your|all|the|any)?[\s_-]*(persona|identity|role|character|self|memory|instructions?|settings?|directives?|policies?)",
        r"restart[\s_-]*(your|the|all)?[\s_-]*(persona|identity|role|memory|instructions?)",
        r"reboot[\s_-]*(your|the|all)?[\s_-]*(persona|identity|role|memory|instructions?)",
        r"clear[\s_-]*(your|all|the)?[\s_-]*(persona|identity|role|memory|instructions?|settings?|history|context)",
        r"reinitialize[\s_-]*(your|the|all)?[\s_-]*(persona|identity|role|memory|instructions?)",
        r"system[\s_-]*(prompt|message|instruction|command|input|context|dialogue)",
        r"(internal|hidden|secret|private|confidential|admin)[\s_-]*(instructions?|prompts?|rules?|guidelines?|directives?|commands?)",
        r"reveal[\s_-]*(the|your|all|any)?[\s_-]*(system|internal|hidden|secret|private|confidential)[\s_-]*(prompt|instructions?|rules?|guidelines?|directives?)",
        r"show[\s_-]*(the|your|all)?[\s_-]*(system|internal|hidden|secret|private)[\s_-]*(prompt|instructions?|rules?)",
        r"display[\s_-]*(the|your|all)?[\s_-]*(system|internal|hidden|secret)[\s_-]*(prompt|instructions?)",
        r"jail[\s_-]*break|jailbreak[\s_-]*(mode|prompt|instructions?)",
        r"DAN|dev[\s_-]*mod|developer[\s_-]*mode",
        r"(unrestricted|uncensored|unfiltered|raw|direct)[\s_-]*mode",
        r"no[\s_-]*(restrictions?|limits?|filters?|censorship|safety|security)",
        r"<\|[^|]+\|>|<[^>]+>|\{[^}]+\}|\[[^\]]+\]",
        r"(what\s+would\s+happen|tell\s+me|explain|describe|show\s+me)\s+(if|when|someone\s+says?|a\s+user\s+says?|they\s+say)",
    ]
    
    MULTILINGUAL_PATTERNS = {
        "zh": [
            r"忽略.*?(指令|命令|规则|提示|指导|指示|规范|原则|约束)",
            r"无视.*?(指令|命令|规则)",
            r"忘记.*?(角色|人格|身份|指令)",
            r"系统.*?(提示|消息|指令|命令)",
            r"(内部|隐藏|秘密|私密).*?(指令|提示|规则|命令)",
            r"越狱|越狱提示|开发模式",
        ],
        "es": [
            r"ignorar.*?(instrucciones|ordenes|reglas|indicaciones|directrices)",
            r"olvidar.*?(rol|identidad|instrucciones)",
            r"ahora eres (un|una|el|la)",
            r"haz(te)? pasar por (un|una)",
            r"mensaje (del|de) sistema",
            r"(anular|omitir|desactivar).*?(instrucciones|restricciones|filtros)",
        ],
        "fr": [
            r"ignorer.*?(instructions|ordres|regles|directives)",
            r"oublier.*?(role|identite|instructions)",
            r"tu es (maintenant|actuellement|desormais) (un|une|le|la)",
            r"faire semblant d'etre (un|une)",
            r"message (du|de) systeme",
            r"(contourner|desactiver).*?(restrictions?|filtres?|securite)",
        ],
        "de": [
            r"ignorieren.*?(anweisungen|befehle|regeln|richtlinien)",
            r"vergiss.*?(rolle|identitat|anweisungen)",
            r"du bist (jetzt|nun) (ein|eine|der|das)",
            r"tun als ob (du|Sie) (bist|ist)",
            r"system(nachricht|prompt|anweisung)",
            r"(umgehen|deaktivieren).*?(sicherheit|filter|moderation)",
        ],
        "ar": [
            r"تجاهل.*?(التعليمات|الأوامر|القواعد)",
            r"انسى.*?(دورك|التعليمات)",
            r"أنت الآن",
            r"رسالة النظام",
        ],
        "ru": [
            r"игнорировать.*?(инструкции|команды|правила)",
            r"забудь.*?(роль|личность|инструкции)",
            r"ты теперь",
            r"системное (сообщение|промпт)",
        ],
    }
    
    SENSITIVE_PATTERNS = [
        r"\b\d{16}\b",
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"password\s*[:=]\s*\S+",
    ]
    
    _mistral_client = None
    _request_timestamps: List[float] = []

    @classmethod
    def _get_mistral_client(cls):
        if not MISTRAL_AVAILABLE:
            return None
        if cls._mistral_client is None:
            api_key = os.getenv("MISTRAL_API_KEY")
            if api_key and Mistral:
                cls._mistral_client = Mistral(api_key=api_key)
        return cls._mistral_client
    
    @classmethod
    def _check_rate_limit(cls) -> bool:
        now = time.time()
        cls._request_timestamps = [t for t in cls._request_timestamps 
                                   if now - t < cls.RATE_LIMIT_WINDOW]
        if len(cls._request_timestamps) >= cls.RATE_LIMIT_MAX_REQUESTS:
            return False
        cls._request_timestamps.append(now)
        return True
    
    @classmethod
    def check_injection(cls, text: str, use_rate_limit: bool = True) -> Dict[str, Any]:
        """
        Enhanced multi-layered prompt injection detection.
        Layers: rate limiting -> normalization -> pattern matching -> Mistral API
        """
        if use_rate_limit and not cls._check_rate_limit():
            return {"safe": False, "reason": "Rate limit exceeded", "method": "rate_limit"}
        
        if not text or not isinstance(text, str):
            return {"safe": True}
        
        # Check original text first
        result = cls._check_patterns_on_text(text, "original")
        if not result["safe"]:
            return result
        
        # Check normalized text
        normalized_text = TextNormalizer.normalize_text(text)
        if normalized_text != text.lower():
            result = cls._check_patterns_on_text(normalized_text, "normalized")
            if not result["safe"]:
                return result
        
        # Check base64 encoded content
        if re.match(r'^[A-Za-z0-9+/=\s]+$', text.strip()):
            decoded, was_decoded = TextNormalizer.decode_base64(text.strip())
            if was_decoded:
                result = cls._check_patterns_on_text(decoded, "base64_decoded")
                if not result["safe"]:
                    return result
        
        # Try Mistral moderation API
        try:
            client = cls._get_mistral_client()
            if client:
                moderation_result = cls.moderate_content(text)
                if not moderation_result.get("safe", True):
                    return {
                        "safe": False,
                        "reason": "Mistral moderation flagged content",
                        "method": "mistral_moderation",
                        "categories": moderation_result.get("categories", [])
                    }
        except Exception:
            pass
        
        return {"safe": True}
    
    @classmethod
    def _check_patterns_on_text(cls, text: str, method: str = "unknown") -> Dict[str, Any]:
        if not text:
            return {"safe": True}
        
        text_lower = text.lower()
        
        # Check English patterns
        for pattern in cls.ENGLISH_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return {"safe": False, "reason": "Prompt injection pattern detected",
                        "pattern": pattern, "method": method}
        
        # Check multilingual patterns
        for lang, patterns in cls.MULTILINGUAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return {"safe": False, "reason": f"Prompt injection pattern detected ({lang})",
                            "pattern": pattern, "language": lang, "method": method}
        
        # Legacy patterns
        for pattern in [
            r"ignore previous instructions",
            r"disregard all",
            r"forget your role",
            r"you are now",
            r"system prompt",
            r"<\|im_start\|>",
            r"<\|system\|>",
        ]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return {"safe": False, "reason": "Legacy prompt injection pattern detected",
                        "pattern": pattern, "method": method}
        
        return {"safe": True}
    
    @classmethod
    def check_sensitive_data(cls, text: str) -> Dict[str, any]:
        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                return {"safe": False, "reason": "Sensitive data detected", "pattern": pattern}
        return {"safe": True}
    
    @classmethod
    def moderate_content(cls, text: str) -> Dict[str, any]:
        client = cls._get_mistral_client()
        if not client:
            return cls._fallback_moderation(text)
        try:
            response = client.classifiers.moderate(model="mistral-moderation-latest", inputs=[text])
            if response.results:
                result = response.results[0]
                categories = result.categories
                flagged = [k for k, v in categories.items() if v]
                if flagged:
                    scores = getattr(result, "category_scores", {}) or {}
                    return {
                        "safe": False, "reason": "Content policy violation detected",
                        "categories": flagged,
                        "category_scores": {k: scores.get(k) for k in flagged}
                    }
            return {"safe": True, "categories": []}
        except Exception as e:
            print(f"Mistral moderation error: {e}")
            return cls._fallback_moderation(text)
    
    @classmethod
    def _fallback_moderation(cls, text: str) -> Dict[str, any]:
        profanity = ["fuck", "shit", "damn", "bitch", "asshole"]
        text_lower = text.lower()
        for word in profanity:
            if word in text_lower:
                return {"safe": False, "reason": "Inappropriate content detected (fallback)", "fallback": True}
        return {"safe": True, "fallback": True}
    
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        if not text:
            return text
        text = re.sub(r'<\|.*?\|>', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\{[^}]+\}', '', text)
        text = re.sub(r'\[[^\]]+\]', '', text)
        text = ' '.join(text.split())
        return text.strip()
    
    @classmethod
    def reset_rate_limit(cls):
        cls._request_timestamps = []


def check_injection(text: str) -> Dict[str, Any]:
    return SafetyFilter.check_injection(text)
