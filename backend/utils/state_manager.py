
import uuid

_STATE = {}


def _default_state():
    return {
        "flow": "idle",
        "step": None,
        "language": None,
        "cart": [],
        "context": {},
        "pending_intent": None,
        "selected_entity": None,
        "completed": False,
    }


def get_or_create_session(session_id=None):
    if session_id and session_id in _STATE:
        return session_id
    new_id = session_id or str(uuid.uuid4())
    _STATE.setdefault(new_id, _default_state())
    return new_id


def get_state(session_id):
    return _STATE.setdefault(session_id, _default_state())


def update_state(session_id, updates):
    state = get_state(session_id)
    state.update(updates)
    return state


def reset_flow(session_id):
    state = get_state(session_id)
    state["flow"] = "idle"
    state["step"] = None
    state["context"] = {}
    state["pending_intent"] = None
    state["language"] = None
    state["selected_entity"] = None
    state["completed"] = False
    return state


def add_to_cart(session_id, item):
    state = get_state(session_id)
    state.setdefault("cart", []).append(item)
    return state["cart"]
