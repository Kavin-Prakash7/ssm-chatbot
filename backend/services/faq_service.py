
from backend.utils.helpers import load_json, normalize_text


_FAQ_CACHE = None


def _load_faq():
    global _FAQ_CACHE
    if _FAQ_CACHE is None:
        data = load_json("data/faq.json")
        _FAQ_CACHE = {
            normalize_text(item["question"]): {
                "answer": item.get("answer", ""),
                "answer_ms": item.get("answer_ms", ""),
            }
            for item in data
        }
    return _FAQ_CACHE


def get_answer(question, language="en"):
    faq = _load_faq().get(normalize_text(question))
    if not faq:
        return None
    if language == "ms" and faq.get("answer_ms"):
        return faq["answer_ms"]
    return faq.get("answer")
