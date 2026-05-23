
import re

from backend.utils.helpers import normalize_text


GREETING_KEYWORDS = {
    "hello",
    "hi",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "hai",
    "helo",
    "salam",
    "selamat pagi",
    "selamat petang",
    "selamat malam",
}

ONBOARDING_KEYWORDS = {
    "help",
    "bantuan",
    "how does this work",
    "how do i use",
    "what can you do",
    "how can you help",
    "start",
    "mula",
    "first time",
    "new here",
    "cara guna",
    "macam mana",
    "panduan",
}

PRICING_KEYWORDS = {
    "pricing",
    "price",
    "cost",
    "fee",
    "fees",
    "charges",
    "harga",
    "berapa harga",
    "berapa caj",
    "berapa kos",
}

FLOW_SIGNAL_MAP = {
    "loan": {
        "action": "loan_from_bank",
        "strong": {
            "bank loan",
            "loan application",
            "loan from bank",
            "business loan",
            "corporate bank account",
            "pinjaman bank",
            "permohonan pinjaman",
            "pembiayaan bank",
        },
        "soft": {
            "loan",
            "financing",
            "finance",
            "pinjaman",
            "pembiayaan",
        },
    },
    "documents": {
        "action": "get_documents",
        "strong": {
            "company documents",
            "ssm documents",
            "get documents",
            "need documents",
            "dokumen syarikat",
            "dokumen ssm",
            "dapatkan dokumen",
            "perlukan dokumen",
        },
        "soft": {
            "document",
            "documents",
            "ctc",
            "non ctc",
            "non-ctc",
            "company profile",
            "certificate of incorporation",
            "register of directors",
            "dokumen",
            "profil syarikat",
            "sijil pemerbadanan",
            "daftar pengarah",
        },
    },
    "company": {
        "action": "check_company",
        "strong": {
            "company search",
            "search company",
            "company information",
            "check company",
            "find company",
            "carian syarikat",
            "semak syarikat",
            "maklumat syarikat",
            "cari syarikat",
        },
        "soft": {
            "company info",
            "company details",
            "business information",
            "company name",
            "syarikat",
            "maklumat perniagaan",
            "nama syarikat",
        },
    },
}

FAQ_TOPIC_ACTIONS = {
    "faq:ctc_vs_non_ctc": {
        "ctc vs non ctc",
        "difference between ctc and non ctc",
        "ctc and non ctc",
        "beza ctc dan non ctc",
        "perbezaan ctc",
    },
    "faq:loan_documents": {
        "loan documents",
        "documents required for loan",
        "documents required for bank",
        "open a corporate bank account",
        "dokumen pinjaman",
        "dokumen untuk bank",
        "dokumen untuk pinjaman",
    },
    "faq:company_status": {
        "company status",
        "is a company active",
        "dissolved company",
        "check if company is active",
        "status syarikat",
        "syarikat aktif",
        "syarikat dibubarkan",
    },
    "faq:director_involvement": {
        "director involvement",
        "verify director",
        "director in multiple companies",
        "check director involvement",
        "penglibatan pengarah",
        "semak pengarah",
        "pengarah dalam syarikat lain",
    },
}

FAQ_GENERAL_KEYWORDS = {
    "faq",
    "question",
    "questions",
    "what is",
    "what are",
    "how to",
    "how can i",
    "can i",
    "bolehkah",
    "apakah",
    "bagaimana",
    "soalan",
}

FAQ_DOMAIN_HINTS = {
    "ssm",
    "document",
    "documents",
    "company",
    "director",
    "loan",
    "bank",
    "ctc",
    "dokumen",
    "syarikat",
    "pengarah",
    "pinjaman",
}

COMPANY_SUFFIX_PATTERN = re.compile(
    r"\b(sdn\s*bhd|sendirian\s+berhad|berhad|bhd|enterprise|trading|holdings|llp|plc)\b"
)


def _matches_keyword(text, keywords):
    return any(re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) for keyword in keywords)


def _looks_like_company_query(text):
    return bool(COMPANY_SUFFIX_PATTERN.search(text))


def _count_matches(text, keywords):
    return sum(1 for keyword in keywords if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text))


def _score_flow_intents(text):
    scores = {}
    for intent_name, config in FLOW_SIGNAL_MAP.items():
        strong_score = _count_matches(text, config["strong"]) * 3
        soft_score = _count_matches(text, config["soft"])
        scores[intent_name] = strong_score + soft_score

    if _looks_like_company_query(text):
        scores["company"] += 3

    return scores


def _build_flow_result(intent_name, confidence):
    return {
        "intent": intent_name,
        "action": FLOW_SIGNAL_MAP[intent_name]["action"],
        "kind": "flow",
        "confidence": confidence,
    }


def detect_intent(message):
    text = normalize_text(message)
    if not text:
        return None

    for action, keywords in FAQ_TOPIC_ACTIONS.items():
        if _matches_keyword(text, keywords):
            return {"intent": "faq", "action": action, "kind": "direct", "confidence": "high"}

    if _matches_keyword(text, PRICING_KEYWORDS):
        return {"intent": "pricing", "action": "view_pricing", "kind": "direct", "confidence": "high"}

    flow_scores = _score_flow_intents(text)
    ranked_flows = sorted(flow_scores.items(), key=lambda item: item[1], reverse=True)
    best_intent, best_score = ranked_flows[0]
    second_score = ranked_flows[1][1] if len(ranked_flows) > 1 else 0

    if best_score >= 4 and best_score - second_score >= 2:
        return _build_flow_result(best_intent, "high")

    if best_score >= 2:
        suggestions = [
            _build_flow_result(intent_name, "medium")
            for intent_name, score in ranked_flows
            if score >= 2
        ]
        if suggestions:
            return {
                "intent": "clarify",
                "action": None,
                "kind": "suggestion",
                "confidence": "medium",
                "suggestions": suggestions[:3],
            }

    if _matches_keyword(text, ONBOARDING_KEYWORDS):
        return {"intent": "onboarding", "action": "main_menu", "kind": "direct", "confidence": "high"}

    if _matches_keyword(text, GREETING_KEYWORDS):
        return {"intent": "greeting", "action": "main_menu", "kind": "direct", "confidence": "high"}

    if _matches_keyword(text, FAQ_GENERAL_KEYWORDS):
        return {"intent": "faq", "action": "faq_general", "kind": "direct", "confidence": "medium"}

    if text.endswith("?") and _matches_keyword(text, FAQ_DOMAIN_HINTS):
        return {"intent": "faq", "action": "faq_general", "kind": "direct", "confidence": "medium"}

    return None
