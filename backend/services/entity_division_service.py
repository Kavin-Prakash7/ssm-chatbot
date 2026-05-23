from functools import lru_cache

from backend.utils.helpers import load_json, normalize_text

DIVISION_KEYWORDS = {
    "banks": {
        "loan",
        "bank loan",
        "bank",
        "pinjaman",
        "finance",
        "financing",
        "pembiayaan",
    },
    "companies": {
        "company",
        "sdn bhd",
        "company profile",
        "corporate",
        "maklumat syarikat",
        "profil syarikat",
    },
    "businesses": {
        "business",
        "enterprise",
        "trading",
        "business registration",
        "perniagaan",
        "pendaftaran perniagaan",
    },
    "llps": {
        "llp",
        "plt",
        "partnership",
        "perkongsian",
    },
}

DIVISION_FLOW_ACTIONS = {
    "banks": "loan_from_bank",
    "companies": "check_company",
    "businesses": "get_documents",
    "llps": "get_documents",
}

DIVISION_LIMIT = 4


@lru_cache()
def _load_entities_by_division():
    data = load_json("data/master_entities.json")
    entities = {}
    for division in ("banks", "businesses", "companies", "llps"):
        entities[division] = data.get(division, [])
    return entities


def detect_division(message):
    if not message:
        return None
    text = normalize_text(message).lower()
    if not text:
        return None
    best_division = None
    best_score = 0
    for division, keywords in DIVISION_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_division = division
    return best_division if best_score else None


def get_entities_for_division(division, limit=DIVISION_LIMIT):
    entities = _load_entities_by_division().get(division) or []
    return entities[:limit]


def get_division_flow_action(division):
    return DIVISION_FLOW_ACTIONS.get(division)
