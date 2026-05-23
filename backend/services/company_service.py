
from backend.utils.helpers import load_json


_ENTITY_CACHE = None


def _load_entities():
    global _ENTITY_CACHE
    if _ENTITY_CACHE is None:
        data = load_json("data/master_entities.json")
        entities = []
        for key in ("companies", "businesses", "llps"):
            for item in data.get(key, []):
                entities.append({"name": item["name"], "type": item["type"]})
        _ENTITY_CACHE = entities
    return _ENTITY_CACHE


def search_entities(query, page=1, page_size=5):
    entities = _load_entities()
    query_lower = query.lower()
    matches = [item for item in entities if query_lower in item["name"].lower()]
    total = len(matches)
    start = (page - 1) * page_size
    end = start + page_size
    return matches[start:end], total
